package com.terrapulse.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Subset of GET /api/climate/risk/{region} from the ML engine.
 */
public record MlRiskResponse(
        String region,
        @JsonProperty("risk_level") String riskLevel,
        Object probabilities) {
}
