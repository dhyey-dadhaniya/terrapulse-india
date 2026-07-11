package com.terrapulse.backend.repository;

import com.terrapulse.backend.entity.AlertLog;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AlertLogRepository extends JpaRepository<AlertLog, Long> {
}
