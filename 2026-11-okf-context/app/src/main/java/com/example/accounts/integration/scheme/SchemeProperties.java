package com.example.accounts.integration.scheme;

import java.time.Duration;
import java.time.LocalTime;

import org.springframework.boot.context.properties.ConfigurationProperties;

/** Payment scheme gateway settings (integrations.scheme.*). */
@ConfigurationProperties("integrations.scheme")
public record SchemeProperties(String url, LocalTime cutoff, Duration timeout) {
}
