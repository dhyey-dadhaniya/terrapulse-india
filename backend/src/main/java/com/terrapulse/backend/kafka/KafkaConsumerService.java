package com.terrapulse.backend.kafka;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.terrapulse.backend.dto.AlertNotification;
import com.terrapulse.backend.dto.IotSensorMessage;
import com.terrapulse.backend.entity.AlertLog;
import com.terrapulse.backend.entity.Region;
import com.terrapulse.backend.entity.SensorReading;
import com.terrapulse.backend.repository.AlertLogRepository;
import com.terrapulse.backend.repository.RegionRepository;
import com.terrapulse.backend.repository.SensorReadingRepository;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeParseException;
import java.util.Optional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

/**
 * Consumes live (or simulated) IoT climate readings from Kafka and stores them.
 *
 * {@code @KafkaListener} means Spring calls this method automatically whenever
 * a new message arrives on the topic — no manual polling loop needed.
 *
 * We look up Region by name (not id) because the Python producer only knows
 * city names; it does not know our Postgres primary keys.
 */
@Service
public class KafkaConsumerService {

    private static final Logger log = LoggerFactory.getLogger(KafkaConsumerService.class);

    private static final double METHANE_ALERT_THRESHOLD = 400.0;
    private static final double SMOKE_ALERT_THRESHOLD = 300.0;
    private static final String ALERTS_TOPIC = "/topic/alerts";

    private final ObjectMapper objectMapper;
    private final RegionRepository regionRepository;
    private final SensorReadingRepository sensorReadingRepository;
    private final AlertLogRepository alertLogRepository;
    private final SimpMessagingTemplate messagingTemplate;

    public KafkaConsumerService(
            ObjectMapper objectMapper,
            RegionRepository regionRepository,
            SensorReadingRepository sensorReadingRepository,
            AlertLogRepository alertLogRepository,
            SimpMessagingTemplate messagingTemplate) {
        this.objectMapper = objectMapper;
        this.regionRepository = regionRepository;
        this.sensorReadingRepository = sensorReadingRepository;
        this.alertLogRepository = alertLogRepository;
        this.messagingTemplate = messagingTemplate;
    }

    @KafkaListener(topics = "iot-climate-stream", groupId = "terrapulse-backend")
    public void consumeIotClimateMessage(String rawMessage) {
        try {
            IotSensorMessage message = objectMapper.readValue(rawMessage, IotSensorMessage.class);
            if (message.regionName() == null || message.regionName().isBlank()) {
                log.warn("Skipping IoT message with missing region_name: {}", rawMessage);
                return;
            }

            Optional<Region> regionOpt = regionRepository.findByNameIgnoreCase(message.regionName());
            if (regionOpt.isEmpty()) {
                log.warn(
                        "Skipping IoT message for unknown region '{}': no matching Region row in DB",
                        message.regionName());
                return;
            }

            Region region = regionOpt.get();
            SensorReading reading = new SensorReading();
            reading.setRegionId(region.getId());
            reading.setMethaneLevel(message.methaneLevel());
            reading.setSmokeDensity(message.smokeDensity());
            reading.setTemperature(message.temperature());
            reading.setTimestamp(parseTimestamp(message.timestamp()));

            SensorReading saved = sensorReadingRepository.save(reading);
            log.info(
                    "IoT reading saved: id={} region={} ({}) methane={} smoke={} temp={}",
                    saved.getId(),
                    region.getName(),
                    region.getId(),
                    saved.getMethaneLevel(),
                    saved.getSmokeDensity(),
                    saved.getTemperature());

            boolean fireLike =
                    (saved.getMethaneLevel() != null && saved.getMethaneLevel() > METHANE_ALERT_THRESHOLD)
                            || (saved.getSmokeDensity() != null
                                    && saved.getSmokeDensity() > SMOKE_ALERT_THRESHOLD);

            if (fireLike) {
                AlertLog alert = new AlertLog();
                alert.setRegionId(region.getId());
                alert.setSeverity("HIGH");
                alert.setMessage(
                        "Emergency: High Smoke & Methane detected in "
                                + region.getName()
                                + " - Potential Forest Fire Alert!");
                alert.setCreatedAt(LocalDateTime.now());
                AlertLog savedAlert = alertLogRepository.save(alert);
                log.warn(
                        "ALERT CREATED: id={} severity={} region={} message={}",
                        savedAlert.getId(),
                        savedAlert.getSeverity(),
                        region.getName(),
                        savedAlert.getMessage());

                // Push to any browser (or other client) subscribed to /topic/alerts.
                messagingTemplate.convertAndSend(
                        ALERTS_TOPIC,
                        new AlertNotification(
                                savedAlert.getId(),
                                savedAlert.getRegionId(),
                                region.getName(),
                                savedAlert.getMessage(),
                                savedAlert.getSeverity(),
                                savedAlert.getCreatedAt()));
            }
        } catch (Exception ex) {
            log.error("Failed to process IoT Kafka message (continuing): {}", rawMessage, ex);
        }
    }

    private LocalDateTime parseTimestamp(String timestamp) {
        if (timestamp == null || timestamp.isBlank()) {
            return LocalDateTime.now();
        }
        try {
            return Instant.parse(timestamp).atZone(ZoneOffset.UTC).toLocalDateTime();
        } catch (DateTimeParseException ignored) {
            // Fall through and try a plain local datetime string.
        }
        try {
            return LocalDateTime.parse(timestamp);
        } catch (DateTimeParseException ex) {
            log.warn("Could not parse timestamp '{}'; using now()", timestamp);
            return LocalDateTime.now();
        }
    }
}
