package com.example.accounts.hidden;

import static com.example.accounts.support.TestUsers.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.LocalDateTime;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import com.example.accounts.payment.QueuedPaymentJob;
import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

class F2HiddenTest extends ApiTest {

    @Autowired
    QueuedPaymentJob queuedJob;

    @Test
    void functional_holderCancelsAQueuedPayment() throws Exception {
        postAs(ALICE, "/api/payments/4/cancel", null).andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(4)).andExpect(jsonPath("$.status").value("CANCELLED"));
        getAs(ALICE, "/api/payments/4").andExpect(jsonPath("$.status").value("CANCELLED"));
    }

    @Test
    void functional_cancelledPaymentIsNeverSent() throws Exception {
        postAs(ALICE, "/api/payments/4/cancel", null).andExpect(status().isOk());
        clock.set(LocalDateTime.of(2026, 10, 7, 6, 0));
        queuedJob.runDue();
        assertThat(scheme.submitted).isEmpty();
        assertThat(ledger.calls).isEmpty();
        getAs(ALICE, "/api/payments/4").andExpect(jsonPath("$.status").value("CANCELLED"));
    }

    @Test
    void functional_otherStatusesConflict() throws Exception {
        postAs(ALICE, "/api/payments/2/cancel", null).andExpect(status().isConflict());
        postAs(ALICE, "/api/payments/3/cancel", null).andExpect(status().isConflict());
        postAs(ALICE, "/api/payments/4/cancel", null).andExpect(status().isOk());
        postAs(ALICE, "/api/payments/4/cancel", null).andExpect(status().isConflict());
    }

    @Test
    void access_onlyTheHolderCancels() throws Exception {
        postAs(SAM, "/api/payments/4/cancel", null).andExpect(status().isForbidden());
        postAs(ADA, "/api/payments/4/cancel", null).andExpect(status().isForbidden());
        postAs(BOB, "/api/payments/4/cancel", null).andExpect(status().isNotFound());
        postAs(GIL, "/api/payments/4/cancel", null).andExpect(status().isNotFound());
        getAs(ALICE, "/api/payments/4").andExpect(jsonPath("$.status").value("QUEUED"));
    }

    @Test
    void access_needsTheWriteScope() throws Exception {
        postWith(TestTokens.of(ALICE).scopes("accounts:read"), "/api/payments/4/cancel", null)
            .andExpect(status().isForbidden());
        getAs(ALICE, "/api/payments/4").andExpect(jsonPath("$.status").value("QUEUED"));
    }
}
