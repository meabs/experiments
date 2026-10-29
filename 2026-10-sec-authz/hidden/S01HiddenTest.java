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


/** Hidden evaluation tests for task S01 (not visible to the agent). Notes on an account. */
class S01HiddenTest extends ApiTest {

    private static final String A1 = "/api/accounts/1/notes";

    @Test
    void functional_newestFirstWithAllFields() throws Exception {
        getAs(ADA, A1).andExpect(status().isOk())
            .andExpect(jsonPath("$[*].id", contains(3, 2, 1)))
            .andExpect(jsonPath("$[0].author").value("u-ada"))
            .andExpect(jsonPath("$[0].body").value("New debit card posted."))
            .andExpect(jsonPath("$[0].internal").value(false))
            .andExpect(jsonPath("$[0].createdAt").exists());
    }

    @Test
    void functional_accountWithoutNotesGivesEmptyList() throws Exception {
        getAs(ADA, "/api/accounts/5/notes").andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(0)));
    }

    @Test
    void allows_ownerSeesTheirNonInternalNotes() throws Exception {
        getAs(ALICE, A1).andExpect(status().isOk()).andExpect(jsonPath("$[*].id", hasItems(3, 1)));
        getAs(ALICE, "/api/accounts/2/notes").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", hasItems(4)));
    }

    @Test
    void allows_assignedSupportSeesInternalNotes() throws Exception {
        getAs(SAM, A1).andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(3, 2, 1)));
    }

    @Test
    void allows_assignedSupportWithAnotherRoleToo() throws Exception {
        getAs(ANA, "/api/accounts/3/notes").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(6, 5)));
    }

    @Test
    void allows_tenantAdminSeesInternalNotes() throws Exception {
        getAs(ADA, "/api/accounts/3/notes").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(6, 5)));
        getAs(GIL, "/api/accounts/4/notes").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(7)));
    }

    @Test
    void denies_ownerNeverGetsInternalNotes() throws Exception {
        getAs(ALICE, A1).andExpect(content().string(not(containsString("Fraud alert"))))
            .andExpect(jsonPath("$[?(@.internal == true)]", hasSize(0)))
            .andExpect(jsonPath("$[*].id", contains(3, 1)));
        getAs(BOB, "/api/accounts/3/notes").andExpect(status().isOk())
            .andExpect(content().string(not(containsString("hardship"))))
            .andExpect(jsonPath("$[*].id", contains(5)));
        getAs(CAROL, "/api/accounts/4/notes").andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(0)));
    }

    @Test
    void denies_otherCustomerGets404() throws Exception {
        getAs(BOB, A1).andExpect(status().isNotFound()).andExpect(content().string(not(containsString("Welcome"))));
    }

    @Test
    void denies_unassignedSupportGets404() throws Exception {
        getAs(SUE, A1).andExpect(status().isNotFound());
        getAs(SAM, "/api/accounts/3/notes").andExpect(status().isNotFound());
    }

    @Test
    void denies_otherTenantGets404() throws Exception {
        getAs(CAROL, A1).andExpect(status().isNotFound());
        getAs(GUS, A1).andExpect(status().isNotFound());
        getAs(GIL, A1).andExpect(status().isNotFound());
        getAs(ADA, "/api/accounts/4/notes").andExpect(status().isNotFound());
    }

    @Test
    void denies_missingAccountGets404() throws Exception {
        getAs(ADA, "/api/accounts/999/notes").andExpect(status().isNotFound());
    }

    @Test
    void denies_unauthenticatedGets401() throws Exception {
        getAnonymous(A1).andExpect(status().isUnauthorized());
    }
}
