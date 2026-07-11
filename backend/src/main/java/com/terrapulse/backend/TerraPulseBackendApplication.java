package com.terrapulse.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class TerraPulseBackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(TerraPulseBackendApplication.class, args);
    }
}
