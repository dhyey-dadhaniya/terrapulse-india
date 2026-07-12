package com.terrapulse.backend.controller;

import java.time.Duration;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;

/**
 * Aggregated health for local demo: backend is UP if this responds; ML engine is
 * probed with a short timeout so a down FastAPI process does not crash us.
 */
@RestController
@RequestMapping("/api/health")
public class SystemHealthController {

    private final String mlEngineBaseUrl;

    public SystemHealthController(@Value("${ml.engine.base-url}") String mlEngineBaseUrl) {
        this.mlEngineBaseUrl = mlEngineBaseUrl;
    }

    @GetMapping("/system")
    public Map<String, String> systemHealth() {
        Map<String, String> status = new LinkedHashMap<>();
        status.put("backend", "UP");
        status.put("mlEngine", probeMlEngine());
        status.put("timestamp", Instant.now().toString());
        return status;
    }

    private String probeMlEngine() {
        try {
            SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
            requestFactory.setConnectTimeout(Duration.ofSeconds(3));
            requestFactory.setReadTimeout(Duration.ofSeconds(3));

            RestClient client = RestClient.builder()
                    .baseUrl(mlEngineBaseUrl)
                    .requestFactory(requestFactory)
                    .build();

            client.get().uri("/health").retrieve().toBodilessEntity();
            return "UP";
        } catch (Exception ex) {
            return "DOWN";
        }
    }
}
