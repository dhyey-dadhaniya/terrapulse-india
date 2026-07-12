package com.terrapulse.backend.controller;

import com.terrapulse.backend.dto.RiskRefreshSummary;
import com.terrapulse.backend.entity.Region;
import com.terrapulse.backend.exception.RegionNotFoundException;
import com.terrapulse.backend.repository.RegionRepository;
import com.terrapulse.backend.service.RegionService;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/regions")
public class RegionController {

    private final RegionRepository regionRepository;
    private final RegionService regionService;

    public RegionController(RegionRepository regionRepository, RegionService regionService) {
        this.regionRepository = regionRepository;
        this.regionService = regionService;
    }

    @GetMapping
    public List<Region> getAllRegions() {
        return regionRepository.findAll();
    }

    @GetMapping("/{id}")
    public Region getRegionById(@PathVariable Long id) {
        return regionRepository
                .findById(id)
                .orElseThrow(() -> new RegionNotFoundException(id));
    }

    @PostMapping
    public ResponseEntity<Region> createRegion(@RequestBody Region region) {
        region.setId(null);
        if (region.getRiskLevel() == null || region.getRiskLevel().isBlank()) {
            region.setRiskLevel("Low");
        }
        if (region.getLastUpdated() == null) {
            region.setLastUpdated(LocalDateTime.now());
        }
        Region saved = regionRepository.save(region);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }

    /**
     * Manually pull latest risk scores from the ML engine for every region and
     * write them into Postgres. Useful for testing before we add a scheduled job.
     */
    @PostMapping("/refresh-risk")
    public RiskRefreshSummary refreshAllRegionsRisk() {
        return regionService.refreshAllRegionsRisk();
    }
}
