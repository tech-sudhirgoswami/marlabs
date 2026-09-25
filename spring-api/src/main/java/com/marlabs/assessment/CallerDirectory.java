package com.marlabs.assessment;

import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.Optional;

@Component
public class CallerDirectory {
    private final Map<String, ApiModels.Caller> callers = Map.of(
        "atlas-employee-01", new ApiModels.Caller("atlas-employee-01", "Atlas", "employee"),
        "atlas-contractor-01", new ApiModels.Caller("atlas-contractor-01", "Atlas", "contractor"),
        "boreal-employee-01", new ApiModels.Caller("boreal-employee-01", "Boreal", "employee")
    );

    public Optional<ApiModels.Caller> find(String callerId) {
        return Optional.ofNullable(callers.get(callerId));
    }
}
