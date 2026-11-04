package com.example.accounts.support;

import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;

/** In tests, the external systems and the clock are replaced by these fakes. {@link ApiTest} resets them per test. */
@TestConfiguration
public class TestIntegrations {

    @Bean @Primary public MutableClock testClock() { return new MutableClock(); }
    @Bean @Primary public FakeScheme fakeScheme() { return new FakeScheme(); }
    @Bean @Primary public FakeFraudScreening fakeFraudScreening() { return new FakeFraudScreening(); }
    @Bean @Primary public FakeLedger fakeLedger() { return new FakeLedger(); }
    @Bean @Primary public FakeNotifications fakeNotifications() { return new FakeNotifications(); }
}
