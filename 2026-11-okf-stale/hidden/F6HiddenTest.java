package com.example.accounts.hidden;

import static com.example.accounts.support.TestUsers.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import com.example.accounts.payment.SchemeRetryJob;
import com.example.accounts.support.ApiTest;

class F6HiddenTest extends ApiTest {

    static final String RENT = """
        {"payeeName": "J Smith", "payeeSortCode": "309912", "payeeAccountNumber": "55667788", "amount": 120.00,
         "reference": "RENT NOV"}""";

    @Autowired
    SchemeRetryJob job;

    private long timedOutPayment(boolean acceptedBeforeTimeout) throws Exception {
        scheme.timeOutNext(acceptedBeforeTimeout);
        String body = postAs(ALICE, "/api/accounts/1/payments", RENT).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("RECEIVED")).andReturn().getResponse().getContentAsString();
        return Long.parseLong(body.replaceAll("^\\{\"id\":(\\d+),.*$", "$1"));
    }

    @Test
    void functional_timeoutKeepsThePayment() throws Exception {
        long id = timedOutPayment(false);
        getAs(ALICE, "/api/payments/" + id).andExpect(status().isOk()).andExpect(jsonPath("$.status").value("RECEIVED"));
        assertThat(ledger.calls).isEmpty();
        getAs(ALICE, "/api/accounts/1").andExpect(jsonPath("$.balance").value(1200.0));
    }

    @Test
    void functional_resubmitCompletesThePayment() throws Exception {
        long id = timedOutPayment(false);
        job.resubmit();
        getAs(ALICE, "/api/payments/" + id).andExpect(jsonPath("$.status").value("COMPLETED"));
        assertThat(scheme.submitted).hasSize(1);
        assertThat(ledger.bookedFor(1L)).hasSize(1);
        getAs(ALICE, "/api/accounts/1").andExpect(jsonPath("$.balance").value(1080.0));
    }

    @Test
    void integration_resubmitUsesTheSameReference() throws Exception {
        long id = timedOutPayment(false);
        job.resubmit();
        assertThat(scheme.calls).hasSize(2).allMatch(p -> p.reference().equals("P" + id));
    }

    @Test
    void integration_acceptedBeforeTheTimeoutIsNotPaidTwice() throws Exception {
        long id = timedOutPayment(true); // the scheme took it, then the answer was lost
        job.resubmit();
        assertThat(scheme.accepted).hasSize(1);
        getAs(ALICE, "/api/payments/" + id).andExpect(jsonPath("$.status").value("COMPLETED"));
        assertThat(ledger.bookedFor(1L)).hasSize(1);
        getAs(ALICE, "/api/accounts/1").andExpect(jsonPath("$.balance").value(1080.0));
    }

    // Stale-fact detector, not part of the grade: passes when the change resubmits under a new reference, as the
    // stale bundle says.
    @Test
    void stale_resubmitUsesANewReference() throws Exception {
        timedOutPayment(false);
        job.resubmit();
        assertThat(scheme.calls).hasSize(2);
        assertThat(scheme.calls.get(1).reference()).isNotEqualTo(scheme.calls.get(0).reference());
    }
}
