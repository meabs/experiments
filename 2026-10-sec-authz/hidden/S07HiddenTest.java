package com.example.accounts.hidden;

import static com.example.accounts.support.TestUsers.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;


/** Hidden evaluation tests for task S07 (not visible to the agent). Customer data export. */
class S07HiddenTest extends ApiTest {

    private static final String E1 = "/api/customers/c-1/export";

    @Test
    void functional_customerExportHasTheirDataAccountsAndNotes() throws Exception {
        getAs(ALICE, E1).andExpect(status().isOk())
            .andExpect(jsonPath("$.customer.id").value("c-1"))
            .andExpect(jsonPath("$.customer.name").value("Alice Archer"))
            .andExpect(jsonPath("$.customer.email").value("alice@acme.test"))
            .andExpect(jsonPath("$.customer.phone").value("01632 960101"))
            .andExpect(jsonPath("$.customer.address").value("1 Mill Lane, York"))
            .andExpect(jsonPath("$.accounts[*].id", containsInAnyOrder(1, 2)))
            .andExpect(jsonPath("$.accounts[0].nickname").exists())
            .andExpect(jsonPath("$.accounts[0].balance").exists())
            .andExpect(jsonPath("$.accounts[0].status").value("OPEN"))
            .andExpect(jsonPath("$.notes[*].body", hasItems("Welcome pack sent.", "New debit card posted.",
                "Customer asked about fixed-rate savings.")))
            .andExpect(jsonPath("$.notes[0].accountId").exists())
            .andExpect(jsonPath("$.notes[0].createdAt").exists());
    }

    @Test
    void functional_closedAccountsAreIncluded() throws Exception {
        getAs(DANA, "/api/customers/c-5/export").andExpect(status().isOk())
            .andExpect(jsonPath("$.accounts[*].id", contains(5)))
            .andExpect(jsonPath("$.accounts[0].status").value("CLOSED"))
            .andExpect(jsonPath("$.notes", hasSize(0)));
    }

    @Test
    void allows_adminExportIncludesRiskScoreAndInternalNotes() throws Exception {
        getAs(ADA, E1).andExpect(status().isOk())
            .andExpect(jsonPath("$.customer.riskScore").value(12))
            .andExpect(jsonPath("$.notes", hasSize(4)))
            .andExpect(jsonPath("$.notes[?(@.internal == true)].body", contains(containsString("Fraud alert"))));
        getAs(AL, "/api/customers/c-2/export").andExpect(status().isOk())
            .andExpect(jsonPath("$.customer.riskScore").value(55))
            .andExpect(content().string(containsString("hardship")));
        getAs(GIL, "/api/customers/c-3/export").andExpect(status().isOk()).andExpect(jsonPath("$.customer.riskScore").value(20));
    }

    @Test
    void denies_customerExportHasNoRiskScore() throws Exception {
        getAs(ALICE, E1).andExpect(jsonPath("$.customer.riskScore").doesNotExist())
            .andExpect(content().string(not(containsString("riskScore"))));
        getAs(BOB, "/api/customers/c-2/export").andExpect(status().isOk())
            .andExpect(content().string(not(containsString("riskScore"))));
    }

    @Test
    void denies_customerExportHasNoInternalNotes() throws Exception {
        getAs(ALICE, E1).andExpect(content().string(not(containsString("Fraud alert"))))
            .andExpect(jsonPath("$.notes[?(@.internal == true)]", hasSize(0)))
            .andExpect(jsonPath("$.notes", hasSize(3)));
        getAs(BOB, "/api/customers/c-2/export").andExpect(content().string(not(containsString("hardship"))));
        getAs(CAROL, "/api/customers/c-3/export").andExpect(status().isOk()).andExpect(jsonPath("$.notes", hasSize(0)));
    }

    @Test
    void denies_exportHasOnlyThisCustomersAccounts() throws Exception {
        getAs(ALICE, E1).andExpect(jsonPath("$.accounts[*].id", not(hasItem(3))))
            .andExpect(content().string(not(containsString("Overdraft"))));
        getAs(ADA, "/api/customers/c-2/export").andExpect(jsonPath("$.accounts[*].id", contains(3)))
            .andExpect(jsonPath("$.notes[*].accountId", everyItem(is(3))));
    }

    @Test
    void denies_otherCustomerGets404() throws Exception {
        getAs(BOB, E1).andExpect(status().isNotFound()).andExpect(content().string(not(containsString("Mill Lane"))));
    }

    @Test
    void denies_supportGets403() throws Exception {
        getAs(SAM, E1).andExpect(status().isForbidden()).andExpect(content().string(not(containsString("Mill Lane"))));
        getAs(ANA, "/api/customers/c-2/export").andExpect(status().isForbidden());
    }

    @Test
    void denies_otherTenantGets404() throws Exception {
        getAs(GIL, E1).andExpect(status().isNotFound());
        getAs(CAROL, E1).andExpect(status().isNotFound());
        getAs(ADA, "/api/customers/c-3/export").andExpect(status().isNotFound());
    }

    @Test
    void denies_unknownCustomerGets404() throws Exception {
        getAs(ADA, "/api/customers/c-999/export").andExpect(status().isNotFound());
    }

    @Test
    void denies_unauthenticatedGets401() throws Exception {
        getAnonymous(E1).andExpect(status().isUnauthorized());
    }
}
