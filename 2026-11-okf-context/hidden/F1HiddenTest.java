package com.example.accounts.hidden;

import static com.example.accounts.support.TestUsers.*;
import static org.hamcrest.Matchers.contains;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;

class F1HiddenTest extends ApiTest {

    @Test
    void functional_ownerListsPaymentsNewestFirst() throws Exception {
        getAs(ALICE, "/api/accounts/1/payments").andExpect(status().isOk())
            .andExpect(jsonPath("$[*].id", contains(4, 3, 2, 1)))
            .andExpect(jsonPath("$[0].payeeName").value("J Smith"))
            .andExpect(jsonPath("$[0].status").value("QUEUED"))
            .andExpect(jsonPath("$[0].executionDate").value("2026-10-07"))
            .andExpect(jsonPath("$[1].reasonCode").value("AC04"));
    }

    @Test
    void functional_statusFilter() throws Exception {
        getAs(ALICE, "/api/accounts/1/payments?status=COMPLETED").andExpect(status().isOk())
            .andExpect(jsonPath("$[*].id", contains(2, 1)));
    }

    @Test
    void functional_unknownStatusIsBadRequest() throws Exception {
        getAs(ALICE, "/api/accounts/1/payments?status=PAID").andExpect(status().isBadRequest());
    }

    @Test
    void functional_onlyThatAccountsPayments() throws Exception {
        getAs(ALICE, "/api/accounts/2/payments").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(5)));
    }

    @Test
    void access_assignedSupportAndAdminSeeThem() throws Exception {
        getAs(SAM, "/api/accounts/1/payments").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(4, 3, 2, 1)));
        getAs(ADA, "/api/accounts/3/payments").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(6)));
    }

    @Test
    void access_othersGetNotFound() throws Exception {
        getAs(BOB, "/api/accounts/1/payments").andExpect(status().isNotFound());
        getAs(SUE, "/api/accounts/1/payments").andExpect(status().isNotFound());
        getAs(GIL, "/api/accounts/1/payments").andExpect(status().isNotFound());
        getAnonymous("/api/accounts/1/payments").andExpect(status().isUnauthorized());
    }
}
