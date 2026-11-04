package com.example.accounts.integration.fraud;

import java.time.Duration;

import org.springframework.boot.context.properties.ConfigurationProperties;

/** Fraud screening service settings (integrations.fraud.*). */
@ConfigurationProperties("integrations.fraud")
public record FraudProperties(String url, Duration timeout) {
}
