package com.example.accounts.config;

import java.time.Clock;
import java.time.ZoneId;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;

/** The service's clock, in UK time. Inject it rather than calling {@code now()}, so tests can set the time. */
@Configuration
@EnableScheduling
public class ClockConfig {

    public static final ZoneId UK = ZoneId.of("Europe/London");

    @Bean
    Clock clock() {
        return Clock.system(UK);
    }
}
