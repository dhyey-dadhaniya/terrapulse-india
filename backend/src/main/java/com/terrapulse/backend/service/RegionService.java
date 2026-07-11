package com.terrapulse.backend.service;

import com.terrapulse.backend.dto.MlRiskResponse;
import com.terrapulse.backend.dto.RiskRefreshSummary;
import com.terrapulse.backend.dto.RiskRefreshSummary.RiskRefreshDetail;
import com.terrapulse.backend.entity.Region;
import com.terrapulse.backend.exception.RegionNotFoundException;
import com.terrapulse.backend.repository.RegionRepository;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.util.UriComponentsBuilder;

@Service
public class RegionService {

    private static final Logger log = LoggerFactory.getLogger(RegionService.class);

    /**
     * Region names the ML engine currently supports. Names outside this set are
     * skipped (logged) instead of calling the ML API.
     */
    private static final Set<String> ML_KNOWN_REGIONS = Set.of(
            "delhi",
            "mumbai",
            "chennai",
            "bengaluru",
            "kolkata",
            "jaipur",
            "nagpur",
            "patna",
            "lucknow",
            "ahmedabad");

    private final RegionRepository regionRepository;
    private final RestClient mlEngineRestClient;

    public RegionService(RegionRepository regionRepository, RestClient mlEngineRestClient) {
        this.regionRepository = regionRepository;
        this.mlEngineRestClient = mlEngineRestClient;
    }

    /**
     * Ask the ML engine for one region's risk and persist the result.
     */
    public Region refreshRegionRisk(Long regionId) {
        Region region = regionRepository
                .findById(regionId)
                .orElseThrow(() -> new RegionNotFoundException(regionId));

        if (!isKnownMlRegion(region.getName())) {
            throw new IllegalArgumentException(
                    "Region '" + region.getName()
                            + "' is not in the ML engine known-region list; skipping.");
        }

        MlRiskResponse prediction = fetchRiskFromMlEngine(region.getName());
        region.setRiskLevel(prediction.riskLevel());
        region.setLastUpdated(LocalDateTime.now());
        return regionRepository.save(region);
    }

    /**
     * Refresh risk for every region in the DB.
     *
     * Failures are caught per region on purpose: one bad name, timeout, or ML
     * outage should not cancel updates for the remaining cities (same idea as
     * processing a batch of API calls and continuing after a single error).
     */
    public RiskRefreshSummary refreshAllRegionsRisk() {
        List<RiskRefreshDetail> details = new ArrayList<>();
        int updated = 0;
        int failed = 0;

        for (Region region : regionRepository.findAll()) {
            try {
                if (!isKnownMlRegion(region.getName())) {
                    String message = "Not in ML engine known-region list; skipped";
                    log.warn("Skipping risk refresh for region id={} name='{}': {}",
                            region.getId(), region.getName(), message);
                    failed++;
                    details.add(new RiskRefreshDetail(
                            region.getId(),
                            region.getName(),
                            "skipped",
                            region.getRiskLevel(),
                            message));
                    continue;
                }

                Region saved = refreshRegionRisk(region.getId());
                updated++;
                details.add(new RiskRefreshDetail(
                        saved.getId(),
                        saved.getName(),
                        "updated",
                        saved.getRiskLevel(),
                        "Risk refreshed from ML engine"));
            } catch (Exception ex) {
                failed++;
                log.warn(
                        "Risk refresh failed for region id={} name='{}': {}",
                        region.getId(),
                        region.getName(),
                        ex.getMessage());
                details.add(new RiskRefreshDetail(
                        region.getId(),
                        region.getName(),
                        "failed",
                        region.getRiskLevel(),
                        ex.getMessage()));
            }
        }

        return new RiskRefreshSummary(updated, failed, details);
    }

    private boolean isKnownMlRegion(String name) {
        return name != null && ML_KNOWN_REGIONS.contains(name.toLowerCase(Locale.ROOT));
    }

    private MlRiskResponse fetchRiskFromMlEngine(String regionName) {
        String path = UriComponentsBuilder
                .fromPath("/api/climate/risk/{region}")
                .buildAndExpand(regionName)
                .encode()
                .toUriString();

        try {
            MlRiskResponse response = mlEngineRestClient
                    .get()
                    .uri(path)
                    .retrieve()
                    .body(MlRiskResponse.class);

            if (response == null || response.riskLevel() == null || response.riskLevel().isBlank()) {
                throw new IllegalStateException("ML engine returned an empty risk_level");
            }
            return response;
        } catch (RestClientException ex) {
            throw new IllegalStateException(
                    "ML engine call failed for '" + regionName + "': " + ex.getMessage(),
                    ex);
        }
    }
}
