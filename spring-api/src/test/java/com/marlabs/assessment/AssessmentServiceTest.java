package com.marlabs.assessment;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AssessmentServiceTest {
    @Mock CallerDirectory callerDirectory;
    @Mock PythonClient pythonClient;

    @Test
    void rejectsUnknownCaller() {
        when(callerDirectory.find("bad")).thenReturn(java.util.Optional.empty());
        var service = new AssessmentService(callerDirectory, pythonClient);
        var ex = assertThrows(AssessmentService.BadRequestException.class,
            () -> service.answer("bad", new ApiModels.AnswerRequest("q","2026-09-21")));
        assertEquals("UNKNOWN_CALLER", ex.code);
    }

    @Test
    void preservesDuplicateAndFailedItems() throws Exception {
        var caller = new ApiModels.Caller("atlas-employee-01","Atlas","employee");
        when(callerDirectory.find("atlas-employee-01")).thenReturn(java.util.Optional.of(caller));

        byte[] a = "Reference: CERT-101\nI request certification reimbursement of INR 18000.".getBytes();
        var f1 = new MockMultipartFile("files","request-01.txt","text/plain",a);
        var f2 = new MockMultipartFile("files","request-06.txt","text/plain",a);
        var f3 = new MockMultipartFile("files","request-08.txt","text/plain",new byte[0]);

        var processed = new PythonClient.ProcessedDocument(
            "Reference: CERT-101", 
            new ApiModels.Extracted("certification reimbursement",18000.0,"INR","CERT-101"),
            new ApiModels.FieldEvidence(null,null,null,null),
            List.of(18000.0));

        when(pythonClient.process("request-01.txt", a)).thenReturn(processed);
        when(pythonClient.process("request-06.txt", a)).thenReturn(processed);
        when(pythonClient.process("request-08.txt", new byte[0]))
            .thenThrow(new PythonClient.ItemDependencyException("EMPTY_FILE","File is empty"));
        when(pythonClient.answer(anyString(), anyString(), any()))
            .thenReturn(new ApiModels.AnswerResponse("ANSWERED","The applicable annual certification reimbursement limit is INR 25000.",
                List.of(new ApiModels.Citation("atlas-cert-current","The annual certification reimbursement limit for employees is INR 25000."))));

        var metadata = new ApiModels.BatchMetadata("demo-01","2026-09-21",
            List.of(new ApiModels.DocumentManifest("request-01","request-01.txt"),
                    new ApiModels.DocumentManifest("request-06","request-06.txt"),
                    new ApiModels.DocumentManifest("request-08","request-08.txt")));

        var response = new AssessmentService(callerDirectory, pythonClient).batch(
            "atlas-employee-01", metadata, List.of(f1,f2,f3));

        assertEquals(3, response.summary().total());
        assertEquals(2, response.summary().completed());
        assertEquals(1, response.summary().failed());
        assertEquals("request-01", response.results().get(1).duplicate_of());
        assertEquals("FAILED", response.results().get(2).processing_status());
    }
}
