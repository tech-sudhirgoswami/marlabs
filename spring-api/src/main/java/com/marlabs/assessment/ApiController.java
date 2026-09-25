package com.marlabs.assessment;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
public class ApiController {
    private final AssessmentService service;
    private final ObjectMapper mapper;

    public ApiController(AssessmentService service, ObjectMapper mapper) {
        this.service = service;
        this.mapper = mapper;
    }

    @PostMapping(value="/answer", consumes=MediaType.APPLICATION_JSON_VALUE)
    public ApiModels.AnswerResponse answer(
            @RequestHeader(value="X-Caller-Id", required=false) String callerId,
            @RequestBody ApiModels.AnswerRequest request) {
        return service.answer(callerId, request);
    }

    @PostMapping(value="/batches", consumes=MediaType.MULTIPART_FORM_DATA_VALUE)
    public ApiModels.BatchResponse batch(
            @RequestHeader(value="X-Caller-Id", required=false) String callerId,
            @RequestPart("metadata") String metadataJson,
            @RequestPart("files") List<MultipartFile> files) throws Exception {
        ApiModels.BatchMetadata metadata = mapper.readValue(metadataJson, ApiModels.BatchMetadata.class);
        return service.batch(callerId, metadata, files);
    }
}
