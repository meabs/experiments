package com.example.accounts.hidden;

import static com.example.accounts.support.TestUsers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.LocalDateTime;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;

class F3HiddenTest extends ApiTest {

    static final String PAY = """
        {"payeeName": "J Smith", "payeeSortCode": "309912", "payeeAccountNumber": "55667788", "amount": %s}""";

    @Test
    void functional_nothingPaidYetToday() throws Exception {
        getAs(ALICE, "/api/accounts/1/payment-allowance").andExpect(status().isOk())
            .andExpect(jsonPath("$.dailyLimit").value(500)).andExpect(jsonPath("$.paidToday").value(0))
            .andExpect(jsonPath("$.remaining").value(500));
    }

    @Test
    void functional_countsTodaysPayments() throws Exception {
        postAs(ALICE, "/api/accounts/1/payments", PAY.formatted("120.00")).andExpect(status().isCreated());
        postAs(ALICE, "/api/accounts/1/payments", PAY.formatted("30.50")).andExpect(status().isCreated());
        getAs(ALICE, "/api/accounts/1/payment-allowance").andExpect(jsonPath("$.paidToday").value(150.5))
            .andExpect(jsonPath("$.remaining").value(349.5));
    }

    @Test
    void functional_rejectedPaymentsDontCount() throws Exception {
        scheme.rejectNext("AC01");
        postAs(ALICE, "/api/accounts/1/payments", PAY.formatted("200.00")).andExpect(status().isCreated());
        getAs(ALICE, "/api/accounts/1/payment-allowance").andExpect(jsonPath("$.paidToday").value(0))
            .andExpect(jsonPath("$.remaining").value(500));
    }

    @Test
    void functional_queuedPaymentsCountOnTheDayTheyAreMade() throws Exception {
        clock.set(LocalDateTime.of(2026, 10, 6, 17, 0));
        postAs(ALICE, "/api/accounts/1/payments", PAY.formatted("100.00")).andExpect(status().isCreated());
        getAs(ALICE, "/api/accounts/1/payment-allowance").andExpect(jsonPath("$.paidToday").value(100))
            .andExpect(jsonPath("$.remaining").value(400));
    }

    @Test
    void functional_agreesWithTheLimitCheck() throws Exception {
        postAs(ALICE, "/api/accounts/1/payments", PAY.formatted("450.00")).andExpect(status().isCreated());
        getAs(ALICE, "/api/accounts/1/payment-allowance").andExpect(jsonPath("$.remaining").value(50));
        postAs(ALICE, "/api/accounts/1/payments", PAY.formatted("50.01")).andExpect(status().isConflict());
        postAs(ALICE, "/api/accounts/1/payments", PAY.formatted("50.00")).andExpect(status().isCreated());
        getAs(ALICE, "/api/accounts/1/payment-allowance").andExpect(jsonPath("$.remaining").value(0));
    }

    @Test
    void functional_ukDayBoundary() throws Exception {
        // 00:30 UK on 6 October is 23:30 UTC on 5 October: a payment made then counts for 6 October.
        clock.set(LocalDateTime.of(2026, 10, 6, 0, 30));
        postAs(ALICE, "/api/accounts/1/payments", PAY.formatted("80.00")).andExpect(status().isCreated());
        clock.set(LocalDateTime.of(2026, 10, 6, 12, 0));
        getAs(ALICE, "/api/accounts/1/payment-allowance").andExpect(jsonPath("$.paidToday").value(80));
    }

    @Test
    void access_staffWhoLookAfterTheAccountSeeIt() throws Exception {
        getAs(SAM, "/api/accounts/1/payment-allowance").andExpect(status().isOk()).andExpect(jsonPath("$.remaining").value(500));
        getAs(ADA, "/api/accounts/3/payment-allowance").andExpect(status().isOk());
        getAs(BOB, "/api/accounts/1/payment-allowance").andExpect(status().isNotFound());
        getAs(GIL, "/api/accounts/1/payment-allowance").andExpect(status().isNotFound());
    }
}
