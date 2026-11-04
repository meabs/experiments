package com.example.accounts.integration.notify;

import org.springframework.boot.context.properties.ConfigurationProperties;

/** Customer notification service settings (integrations.notifications.*). */
@ConfigurationProperties("integrations.notifications")
public record NotificationProperties(String url) {
}
