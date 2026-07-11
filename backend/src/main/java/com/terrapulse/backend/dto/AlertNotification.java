package com.terrapulse.backend.dto;

import java.time.LocalDateTime;

/**
 * Payload pushed to WebSocket subscribers on /topic/alerts.
 */
public record AlertNotification(
        Long id,
        Long regionId,
        String regionName,
        String message,
        String severity,
        LocalDateTime createdAt) {
}
