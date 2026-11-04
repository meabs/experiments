package com.example.accounts.hidden;

import static com.example.accounts.support.TestUsers.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.LocalDateTime;

import org.junit.jupiter.api.Test;

import com.example.accounts.integration.notify.Notification;
import com.example.accounts.support.ApiTest;

class F7HiddenTest extends ApiTest {

    static final String RENT = """
        {"payeeName": "J Smith", "payeeSortCode": "309912", "payeeAccountNumber": "55667788", "amount": 120.00,
         "reference": "RENT NOV"}""";

    private Notification queued() throws Exception {
        clock.set(LocalDateTime.of(2026, 10, 6, 17, 0));
        postAs(ALICE, "/api/accounts/1/payments", RENT).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("QUEUED"));
        assertThat(notifications.sent).hasSize(1);
        return notifications.sent.get(0);
    }

    private Notification rejected() throws Exception {
        scheme.rejectNext("AC01");
        postAs(ALICE, "/api/accounts/1/payments", RENT).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("REJECTED"));
        assertThat(notifications.sent).hasSize(1);
        return notifications.sent.get(0);
    }

    @Test
    void functional_queuedPaymentIsNotified() throws Exception {
        Notification n = queued();
        assertThat(n.userId()).isEqualTo("u-alice");
        assertThat(n.params().values()).anyMatch(v -> v.contains("120")).anyMatch(v -> v.contains("J Smith"));
    }

    @Test
    void functional_rejectedPaymentIsNotified() throws Exception {
        Notification n = rejected();
        assertThat(n.userId()).isEqualTo("u-alice");
        assertThat(n.params().values()).anyMatch(v -> v.contains("120")).anyMatch(v -> v.contains("J Smith"));
    }

    @Test
    void functional_sentPaymentStillGetsOneMessage() throws Exception {
        postAs(ALICE, "/api/accounts/1/payments", RENT).andExpect(jsonPath("$.status").value("COMPLETED"));
        assertThat(notifications.sent).hasSize(1);
        assertThat(notifications.sent.get(0).template()).isEqualTo("PAYMENT_SENT");
    }

    @Test
    void functional_notificationFailureDoesNotFailThePayment() throws Exception {
        notifications.failNext();
        clock.set(LocalDateTime.of(2026, 10, 6, 17, 0));
        postAs(ALICE, "/api/accounts/1/payments", RENT).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("QUEUED"));
    }

    @Test
    void integration_queuedUsesTheServicesTemplate() throws Exception {
        assertThat(queued().template()).isEqualTo("PAYMENT_QUEUED");
    }

    @Test
    void integration_rejectedUsesTheServicesTemplate() throws Exception {
        assertThat(rejected().template()).isEqualTo("PAYMENT_FAILED");
    }

    @Test
    void integration_neverTheFullAccountNumber() throws Exception {
        Notification q = queued();
        notifications.reset();
        clock.reset();
        Notification r = rejected();
        for (Notification n : new Notification[] {q, r}) {
            assertThat(n.params().values()).noneMatch(v -> v.contains("31926819") || v.contains("401122"));
        }
    }
}
