package com.example.accounts.integration.ledger;

import java.time.Duration;

import org.springframework.boot.context.properties.ConfigurationProperties;

/** Core ledger settings (integrations.ledger.*). */
@ConfigurationProperties("integrations.ledger")
public record LedgerProperties(String url, Duration timeout) {
}
