package com.example.accounts.support;

import java.time.Clock;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;

import com.example.accounts.config.ClockConfig;

/** A clock tests can set. Starts at {@link #DEFAULT}: Tuesday 6 October 2026, 10:00 UK time. */
public class MutableClock extends Clock {

    public static final LocalDateTime DEFAULT = LocalDateTime.of(2026, 10, 6, 10, 0);

    private Instant instant;

    public MutableClock() {
        reset();
    }

    public void reset() {
        set(DEFAULT);
    }

    /** Sets the time, in UK time. */
    public void set(LocalDateTime ukTime) {
        this.instant = ukTime.atZone(ClockConfig.UK).toInstant();
    }

    @Override
    public ZoneId getZone() {
        return ClockConfig.UK;
    }

    @Override
    public Clock withZone(ZoneId zone) {
        throw new UnsupportedOperationException();
    }

    @Override
    public Instant instant() {
        return instant;
    }
}
