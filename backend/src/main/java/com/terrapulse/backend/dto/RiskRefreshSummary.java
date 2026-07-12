package com.terrapulse.backend.dto;

import java.util.List;

public record RiskRefreshSummary(
        int updated,
        int failed,
        List<RiskRefreshDetail> details) {

    public record RiskRefreshDetail(
            Long id,
            String name,
            String status,
            String riskLevel,
            String message) {
    }
}
