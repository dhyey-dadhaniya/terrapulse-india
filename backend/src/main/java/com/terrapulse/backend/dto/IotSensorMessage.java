package com.terrapulse.backend.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * One IoT reading as published by ml-engine/iot_simulator.py onto Kafka.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record IotSensorMessage(
        @JsonProperty("region_name") String regionName,
        @JsonProperty("methane_level") Double methaneLevel,
        @JsonProperty("smoke_density") Double smokeDensity,
        @JsonProperty("temperature") Double temperature,
        @JsonProperty("timestamp") String timestamp) {
}
