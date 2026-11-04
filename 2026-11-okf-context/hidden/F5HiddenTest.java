package com.example.accounts.hidden;

import static com.example.accounts.support.TestUsers.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import com.example.accounts.payment.LedgerRetryJob;
import com.example.accounts.support.ApiTest;

class F5HiddenTest extends ApiTest {

    static final String RENT = """
        {"payeeName": "J Smith", "payeeSortCode": "309912", "payeeAccountNumber": "55667788", "amount": 120.00,
         "reference": "RENT NOV"}""";

    @Autowired
    LedgerRetryJob job;

    private long newFailedPayment(boolean bookedBeforeTimeout) throws Exception {
        ledger.timeOutNext(1, bookedBeforeTimeout);
        String body = postAs(ALICE, "/api/accounts/1/payments", RENT).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("POSTING_FAILED")).andReturn().getResponse().getContentAsString();
        return Long.parseLong(body.replaceAll("^\\{\"id\":(\\d+),.*$", "$1"));
    }

    @Test
    void functional_retrySucceeds() throws Exception {
        long id = newFailedPayment(false);
        job.retryFailed();
        getAs(ALICE, "/api/payments/" + id).andExpect(jsonPath("$.status").value("COMPLETED"));
        assertThat(ledger.bookedFor(1L)).hasSize(1);
    }

    @Test
    void functional_retryDoesNotSendToTheSchemeAgainOrDebitTwice() throws Exception {
        newFailedPayment(false);
        job.retryFailed();
        assertThat(scheme.submitted).hasSize(1);
        getAs(ALICE, "/api/accounts/1").andExpect(jsonPath("$.balance").value(1080.0));
    }

    @Test
    void functional_atMostThreeRetries() throws Exception {
        long id = newFailedPayment(false);
        ledger.timeOutNext(100, false);
        for (int i = 0; i < 6; i++) {
            job.retryFailed();
        }
        assertThat(ledger.calls.stream().filter(p -> p.accountId().equals(1L))).hasSize(4); // the first attempt and three retries
        getAs(ALICE, "/api/payments/" + id).andExpect(jsonPath("$.status").value("POSTING_FAILED"));
    }

    @Test
    void integration_timedOutButBookedIsNotBookedTwice() throws Exception {
        long id = newFailedPayment(true);
        job.retryFailed();
        getAs(ALICE, "/api/payments/" + id).andExpect(jsonPath("$.status").value("COMPLETED"));
        assertThat(ledger.bookedFor(1L)).hasSize(1);
    }

    @Test
    void integration_retryReusesTheOriginalReference() throws Exception {
        job.retryFailed(); // payment 6 in data.sql has been POSTING_FAILED since 30 September
        assertThat(ledger.calls).filteredOn(p -> p.accountId().equals(3L)).isNotEmpty()
            .allMatch(p -> p.reference().equals("a6f1c2d0-1111-4c1e-9a01-000000000006"));
        getAs(BOB, "/api/payments/6").andExpect(jsonPath("$.status").value("COMPLETED"));
    }
}
