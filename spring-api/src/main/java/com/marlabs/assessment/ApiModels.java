package com.marlabs.assessment;

import java.util.List;
import java.util.Map;

public final class ApiModels {
    private ApiModels() {}

    public record AnswerRequest(String question, String as_of) {}
    public record Citation(String chunk_id, String quote) {}
    public record AnswerResponse(String status, String answer, List<Citation> citations) {}

    public record BatchMetadata(String batch_id, String as_of, List<DocumentManifest> documents) {}
    public record DocumentManifest(String document_id, String filename) {}

    public record Extracted(String benefit, Double amount, String currency, String reference) {}
    public record FieldEvidence(Map<String,String> benefit, Map<String,String> amount,
                                 Map<String,String> currency, Map<String,String> reference) {}
    public record PolicyResult(String status, String answer, List<Citation> citations) {}
    public record ErrorBody(String code, String message) {}

    public record BatchItem(
        String document_id,
        String processing_status,
        Extracted extracted,
        FieldEvidence field_evidence,
        PolicyResult policy,
        boolean review_required,
        List<String> issues,
        String duplicate_of,
        ErrorBody error
    ) {}

    public record BatchSummary(int total, int completed, int failed) {}
    public record BatchResponse(String batch_id, BatchSummary summary, List<BatchItem> results) {}

    public record PythonAnswerRequest(String question, String as_of, Caller caller) {}
    public record Caller(String caller_id, String tenant, String role) {}
}
