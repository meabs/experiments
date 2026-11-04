package com.example.accounts;

import static com.example.accounts.support.TestUsers.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.LocalDateTime;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

class PaymentApiTest extends ApiTest {

    static final String RENT = """
        {"payeeName": "J Smith", "payeeSortCode": "309912", "payeeAccountNumber": "55667788", "amount": 120.00,
         "reference": "RENT NOV"}""";

    @Test
    void ownerPaysSomeone() throws Exception {
        postAs(ALICE, "/api/accounts/1/payments", RENT).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("COMPLETED")).andExpect(jsonPath("$.executionDate").value("2026-10-06"));
        assertThat(scheme.submitted).hasSize(1);
        assertThat(ledger.bookedFor(1L)).hasSize(1);
        assertThat(notifications.sent).hasSize(1);
    }

    @Test
    void afterTheCutOffThePaymentIsQueuedForTheNextWorkingDay() throws Exception {
        clock.set(LocalDateTime.of(2026, 10, 9, 16, 0)); // a Friday
        postAs(ALICE, "/api/accounts/1/payments", RENT).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("QUEUED")).andExpect(jsonPath("$.executionDate").value("2026-10-12"));
        assertThat(scheme.submitted).isEmpty();
    }

    @Test
    void schemeRejectionIsRecorded() throws Exception {
        scheme.rejectNext("AC01");
        postAs(ALICE, "/api/accounts/1/payments", RENT).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("REJECTED")).andExpect(jsonPath("$.reasonCode").value("AC01"));
        assertThat(ledger.calls).isEmpty();
    }

    @Test
    void ledgerTimeoutLeavesThePaymentForOperations() throws Exception {
        ledger.timeOutNext(1, false);
        postAs(ALICE, "/api/accounts/1/payments", RENT).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("POSTING_FAILED"));
        assertThat(scheme.submitted).hasSize(1);
    }

    @Test
    void overTheDailyLimitConflicts() throws Exception {
        postAs(ALICE, "/api/accounts/1/payments", RENT.replace("120.00", "501.00")).andExpect(status().isConflict());
    }

    @Test
    void supportCannotPayFromAnAccount() throws Exception {
        postAs(SAM, "/api/accounts/1/payments", RENT).andExpect(status().isForbidden());
    }

    @Test
    void paymentsNeedTheWriteScope() throws Exception {
        postWith(TestTokens.of(ALICE).scopes("accounts:read"), "/api/accounts/1/payments", RENT)
            .andExpect(status().isForbidden());
    }

    @Test
    void anotherCustomersPaymentIsNotFound() throws Exception {
        getAs(ALICE, "/api/payments/1").andExpect(status().isOk()).andExpect(jsonPath("$.payeeName").value("Northern Power"));
        getAs(BOB, "/api/payments/1").andExpect(status().isNotFound());
    }

    @Test
    void queuedPaymentsAreSentOnTheirDate() throws Exception {
        clock.set(LocalDateTime.of(2026, 10, 7, 6, 0));
        queuedJob.runDue();
        getAs(ALICE, "/api/payments/4").andExpect(jsonPath("$.status").value("COMPLETED"));
        assertThat(scheme.submitted).hasSize(1);
    }

    @org.springframework.beans.factory.annotation.Autowired
    com.example.accounts.payment.QueuedPaymentJob queuedJob;
}
