package com.marlabs.assessment;

import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.security.MessageDigest;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class AssessmentService {
    private final CallerDirectory callerDirectory;
    private final PythonClient pythonClient;

    public AssessmentService(CallerDirectory callerDirectory, PythonClient pythonClient) {
        this.callerDirectory = callerDirectory;
        this.pythonClient = pythonClient;
    }

    public ApiModels.AnswerResponse answer(String callerId, ApiModels.AnswerRequest req) {
        ApiModels.Caller caller = requireCaller(callerId);
        validateDate(req.as_of());
        if (req.question() == null || req.question().isBlank()) {
            throw new BadRequestException("INVALID_QUESTION", "question must be non-empty");
        }
        return pythonClient.answer(req.question(), req.as_of(), caller);
    }

    public ApiModels.BatchResponse batch(String callerId, ApiModels.BatchMetadata metadata,
                                         List<MultipartFile> files) {
        ApiModels.Caller caller = requireCaller(callerId);
        validateDate(metadata.as_of());
        validateManifest(metadata, files);

        Map<String, MultipartFile> byFilename = files.stream()
            .collect(Collectors.toMap(MultipartFile::getOriginalFilename, f -> f, (a,b) -> a));

        List<ApiModels.BatchItem> results = new ArrayList<>();
        Map<String, String> digestToDocumentId = new HashMap<>();

        for (ApiModels.DocumentManifest doc : metadata.documents()) {
            MultipartFile file = byFilename.get(doc.filename());
            String duplicateOf = null;
            try {
                byte[] bytes = file.getBytes();
                String digest = sha256(bytes);
                duplicateOf = digestToDocumentId.putIfAbsent(digest, doc.document_id());

                PythonClient.ProcessedDocument p = pythonClient.process(doc.filename(), bytes);

                boolean ambiguousAmount = p.numericAmounts().stream().distinct().count() > 1;
                List<String> issues = new ArrayList<>();
                issues.add("Human review is mandatory for every submitted request.");
                issues.add("The annual policy limit does not establish remaining balance, expense eligibility, or payable amount.");

                if (ambiguousAmount) {
                    issues.add("Multiple different amounts are stated in the request; the amount remains unresolved.");
                }
                if (p.extracted().benefit() == null) {
                    issues.add("Requested benefit could not be identified from the submitted text.");
                }
                if (p.extracted().reference() == null) {
                    issues.add("Reference is missing or unresolved.");
                }

                ApiModels.PolicyResult policy = null;
                if (p.extracted().benefit() != null) {
                    String policyQuestion = policyQuestionFor(p.extracted().benefit());
                    try {
                        ApiModels.AnswerResponse answerResponse =
                            pythonClient.answer(policyQuestion, metadata.as_of(), caller);
                        policy = new ApiModels.PolicyResult(
                            answerResponse.status(), answerResponse.answer(), answerResponse.citations());
                    } catch (PythonClient.DependencyException ex) {
                        results.add(failed(doc.document_id(), ex.code, ex.getMessage(), duplicateOf));
                        continue;
                    }
                    if (policy != null && "INSUFFICIENT_EVIDENCE".equals(policy.status())) {
                        issues.add("No eligible policy evidence supports the requested benefit in the supplied policy corpus.");
                    } else if (policy != null && "CONFLICT".equals(policy.status())) {
                        issues.add("Multiple simultaneously applicable approved policy passages disagree; no precedence rule was invented.");
                    }
                }

                results.add(new ApiModels.BatchItem(
                    doc.document_id(), "COMPLETED", p.extracted(), p.evidence(), policy,
                    true, issues, duplicateOf, null
                ));
            } catch (PythonClient.ItemDependencyException ex) {
                results.add(failed(doc.document_id(), ex.code, ex.getMessage(), duplicateOf));
            } catch (Exception ex) {
                results.add(failed(doc.document_id(), "PROCESSING_FAILED", "Item processing failed", null));
            }
        }

        int failed = (int) results.stream().filter(r -> "FAILED".equals(r.processing_status())).count();
        return new ApiModels.BatchResponse(
            metadata.batch_id(),
            new ApiModels.BatchSummary(results.size(), results.size() - failed, failed),
            results
        );
    }

    private ApiModels.BatchItem failed(String id, String code, String message, String duplicateOf) {
        return new ApiModels.BatchItem(id, "FAILED", null, null, null, true,
            List.of("Technical processing failure; policy findings were not produced."),
            duplicateOf, new ApiModels.ErrorBody(code, message));
    }

    private String policyQuestionFor(String benefit) {
        return switch (benefit) {
            case "certification reimbursement" -> "What is my annual certification reimbursement limit?";
            case "home-office allowance" -> "What is my annual home-office allowance?";
            case "external training" -> "What policy applies to external training?";
            case "wellness benefit" -> "What wellness benefit am I entitled to?";
            case "travel" -> "What travel policy applies?";
            default -> "What policy applies to this benefit?";
        };
    }

    private ApiModels.Caller requireCaller(String callerId) {
        if (callerId == null || callerId.isBlank()) {
            throw new BadRequestException("MISSING_CALLER", "X-Caller-Id is required");
        }
        return callerDirectory.find(callerId)
            .orElseThrow(() -> new BadRequestException("UNKNOWN_CALLER", "Unknown caller"));
    }

    private void validateDate(String asOf) {
        if (asOf == null) throw new BadRequestException("INVALID_AS_OF", "as_of is required");
        try { LocalDate.parse(asOf); }
        catch (DateTimeParseException e) {
            throw new BadRequestException("INVALID_AS_OF", "as_of must be YYYY-MM-DD");
        }
    }

    private void validateManifest(ApiModels.BatchMetadata metadata, List<MultipartFile> files) {
        if (metadata == null || metadata.batch_id() == null || metadata.batch_id().isBlank()
                || metadata.documents() == null) {
            throw new BadRequestException("INVALID_METADATA", "Invalid batch metadata");
        }
        Set<String> ids = new HashSet<>();
        Set<String> names = new HashSet<>();
        for (var d : metadata.documents()) {
            if (d.document_id() == null || d.filename() == null
                    || !ids.add(d.document_id()) || !names.add(d.filename())) {
                throw new BadRequestException("DUPLICATE_MANIFEST_IDENTIFIER",
                    "document_id and filename must be unique");
            }
        }
        if (files == null || files.size() != metadata.documents().size()) {
            throw new BadRequestException("FILE_MANIFEST_MISMATCH",
                "Missing or extra file parts");
        }
        Set<String> uploaded = files.stream().map(MultipartFile::getOriginalFilename).collect(Collectors.toSet());
        if (!uploaded.equals(names)) {
            throw new BadRequestException("FILE_MANIFEST_MISMATCH",
                "Every uploaded filename must match one manifest entry");
        }
    }

    private String sha256(byte[] bytes) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(bytes);
        return HexFormat.of().formatHex(digest);
    }

    public static class BadRequestException extends RuntimeException {
        public final String code;
        public BadRequestException(String code, String message) { super(message); this.code = code; }
    }
}
