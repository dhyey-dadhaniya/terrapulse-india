package com.terrapulse.backend.config;

import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

@Configuration
public class MlEngineConfig {

    /**
     * RestClient talks to the Python ML engine over HTTP — same idea as our
     * Python AQICN fetcher calling an external API. We use RestClient (not
     * WebClient/WebFlux) because our controllers are plain synchronous MVC
     * and RestClient is the modern blocking client already on the classpath
     * via spring-boot-starter-web — no extra reactive dependency needed.
     */
    @Bean
    RestClient mlEngineRestClient(
            RestClient.Builder builder,
            @Value("${ml.engine.base-url}") String baseUrl) {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(Duration.ofSeconds(5));
        requestFactory.setReadTimeout(Duration.ofSeconds(5));

        return builder
                .baseUrl(baseUrl)
                .requestFactory(requestFactory)
                .build();
    }
}
