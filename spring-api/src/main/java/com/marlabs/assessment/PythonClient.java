package com.marlabs.assessment;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;

import java.util.Base64;
import java.util.List;
import java.util.Map;
import org.springframework.http.client.SimpleClientHttpRequestFactory;

@Component
public class PythonClient {
    private final RestClient client;
    private final ObjectMapper mapper;
    private final long timeoutMs;

    public PythonClient(
            @Value("${python.service-url}") String baseUrl,
            @Value("${python.timeout-ms:5000}") long timeoutMs,
            ObjectMapper mapper) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout((int) timeoutMs);
        factory.setReadTimeout((int) timeoutMs);
        this.client = RestClient.builder().baseUrl(baseUrl).requestFactory(factory).build();
        this.mapper = mapper;
        this.timeoutMs = timeoutMs;
    }

    public ApiModels.AnswerResponse answer(String question, String asOf, ApiModels.Caller caller) {
        var body = new ApiModels.PythonAnswerRequest(question, asOf, caller);
        try {
            return client.post()
                .uri("/internal/answer")
                .contentType(MediaType.APPLICATION_JSON)
                .body(body)
                .retrieve()
                .body(ApiModels.AnswerResponse.class);
        } catch (Exception e) {
            throw new DependencyException("PYTHON_SERVICE_UNAVAILABLE", "Python service dependency failed");
        }
    }

    public ProcessedDocument process(String filename, byte[] bytes) {
        try {
            String b64 = Base64.getEncoder().encodeToString(bytes);
            Map<String,String> body = Map.of("filename", filename, "content_b64", b64);
            ResponseEntity<String> response = client.post()
                .uri("/internal/process")
                .contentType(MediaType.APPLICATION_JSON)
                .body(body)
                .retrieve()
                .toEntity(String.class);

            JsonNode n = mapper.readTree(response.getBody());
            ApiModels.Extracted extracted = mapper.treeToValue(n.get("extracted"), ApiModels.Extracted.class);
            ApiModels.FieldEvidence evidence = mapper.treeToValue(n.get("field_evidence"), ApiModels.FieldEvidence.class);
            String text = n.get("text").asText();
            List<Double> amounts = mapper.convertValue(n.get("numeric_amounts"), mapper.getTypeFactory().constructCollectionType(List.class, Double.class));
            return new ProcessedDocument(text, extracted, evidence, amounts);
        } catch (org.springframework.web.client.HttpStatusCodeException e) {
            String code = "PROCESSING_FAILED";
            try {
                JsonNode n = mapper.readTree(e.getResponseBodyAsString());
                if (n.has("detail")) code = n.get("detail").asText();
            } catch (Exception ignored) {
                // Keep a stable safe error code.
            }
            throw new ItemDependencyException(code, safeMessage(code));
        } catch (Exception e) {
            throw new ItemDependencyException("PROCESSING_FAILED", "Document processing failed");
        }
    }

    private String safeMessage(String code) {
        return switch (code) {
            case "EMPTY_FILE" -> "File is empty";
            case "UNREADABLE_FILE" -> "File is unreadable";
            case "INVALID_UTF8" -> "File is not valid UTF-8";
            case "PDF_EXTRACTION_FAILED" -> "PDF extraction failed";
            default -> "Document processing failed";
        };
    }

    public record ProcessedDocument(String text, ApiModels.Extracted extracted,
                                    ApiModels.FieldEvidence evidence, List<Double> numericAmounts) {}
    public static class DependencyException extends RuntimeException {
        public final String code;
        public DependencyException(String code, String message) { super(message); this.code = code; }
    }
    public static class ItemDependencyException extends RuntimeException {
        public final String code;
        public ItemDependencyException(String code, String message) { super(message); this.code = code; }
    }
}
