package com.terrapulse.backend.scheduler;

import com.terrapulse.backend.dto.RiskRefreshSummary;
import com.terrapulse.backend.service.RegionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * Periodically asks the ML engine for fresh risk levels and writes them to the DB.
 *
 * {@code @Scheduled} tells Spring to run this method on a timer in the background
 * (no HTTP call needed). {@code fixedRate} is the gap from the *start* of one run
 * to the *start* of the next — e.g. fixedRate = 1_800_000 means every 1,800,000 ms
 * = 30 minutes.
 *
 * fixedRate = 1_800_000 → run about every 30 minutes from start-of-run to start-of-run.
 */
@Component
public class RiskRefreshScheduler {

    private static final Logger log = LoggerFactory.getLogger(RiskRefreshScheduler.class);

    private final RegionService regionService;

    public RiskRefreshScheduler(RegionService regionService) {
        this.regionService = regionService;
    }

    @Scheduled(fixedRate = 1_800_000)
    public void refreshRiskOnSchedule() {
        log.info("Scheduled risk refresh started");
        try {
            RiskRefreshSummary summary = regionService.refreshAllRegionsRisk();
            log.info(
                    "Scheduled risk refresh completed: updated={} failed={}",
                    summary.updated(),
                    summary.failed());
        } catch (Exception ex) {
            log.error("Scheduled risk refresh failed; will retry on next interval", ex);
        }
    }
}
