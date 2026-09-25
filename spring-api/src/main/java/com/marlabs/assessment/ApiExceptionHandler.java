package com.marlabs.assessment;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler(AssessmentService.BadRequestException.class)
    public ResponseEntity<?> badRequest(AssessmentService.BadRequestException e) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
            .body(Map.of("error", Map.of("code", e.code, "message", e.getMessage())));
    }

    @ExceptionHandler(PythonClient.DependencyException.class)
    public ResponseEntity<?> dependency(PythonClient.DependencyException e) {
        return ResponseEntity.status(HttpStatus.BAD_GATEWAY)
            .body(Map.of("error", Map.of("code", e.code, "message", e.getMessage())));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<?> generic(Exception e) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
            .body(Map.of("error", Map.of("code", "INVALID_REQUEST", "message", "Request could not be processed")));
    }
}
