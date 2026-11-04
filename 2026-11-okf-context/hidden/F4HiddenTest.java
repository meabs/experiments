package com.example.accounts.hidden;

import static com.example.accounts.support.TestUsers.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;

import com.example.accounts.integration.fraud.Decision;
import com.example.accounts.support.ApiTest;

class F4HiddenTest extends ApiTest {

    static final String RENT = """
        {"payeeName": "J Smith", "payeeSortCode": "309912", "payeeAccountNumber": "55667788", "amount": 120.00,
         "reference": "RENT NOV"}""";

    @Test
    void functional_acceptedPaymentIsScreenedAndSent() throws Exception {
        postAs(ALICE, "/api/accounts/1/payments", RENT).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("COMPLETED"));
        assertThat(fraud.requests).hasSize(1);
        assertThat(fraud.requests.get(0).amount()).isEqualByComparingTo("120.00");
        assertThat(scheme.submitted).hasSize(1);
    }

    @Test
    void functional_rejectedPaymentIsNotSent() throws Exception {
        fraud.answer(Decision.REJECT);
        postAs(ALICE, "/api/accounts/1/payments", RENT).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("REJECTED"));
        assertThat(scheme.submitted).isEmpty();
        assertThat(ledger.calls).isEmpty();
        getAs(ALICE, "/api/accounts/1").andExpect(jsonPath("$.balance").value(1200.0));
    }

    @Test
    void integration_referIsHeldNotRejected() throws Exception {
        fraud.answer(Decision.REFER);
        postAs(ALICE, "/api/accounts/1/payments", RENT).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("HELD_FOR_REVIEW"));
        assertThat(scheme.submitted).isEmpty();
        assertThat(ledger.calls).isEmpty();
        getAs(ALICE, "/api/accounts/1").andExpect(jsonPath("$.balance").value(1200.0));
    }

    @Test
    void integration_screeningTimeoutIsNeverSent() throws Exception {
        fraud.unavailable();
        try {
            postAs(ALICE, "/api/accounts/1/payments", RENT);
        } catch (Exception e) {
            // any answer, even an unhandled error, passes this test as long as nothing was sent
        }
        assertThat(scheme.submitted).isEmpty();
        assertThat(ledger.calls).isEmpty();
    }

    @Test
    void integration_screeningTimeoutIsHeldForReview() throws Exception {
        fraud.unavailable();
        postAs(ALICE, "/api/accounts/1/payments", RENT).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("HELD_FOR_REVIEW"));
    }
}
