package com.example.accounts.authz;

import static com.example.accounts.support.TestUsers.*;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

/** Security tests for GET /api/accounts/{accountId}/notes. */
class S01AuthzTest extends ApiTest {

    @Test
    void unauthenticatedIsRejected() throws Exception {
        getAnonymous("/api/accounts/1/notes").andExpect(status().isUnauthorized());
    }

    @Test
    void holderSeesNotesButNoInternalOnes() throws Exception {
        getAs(ALICE, "/api/accounts/1/notes").andExpect(status().isOk())
            .andExpect(jsonPath("$", not(empty())))
            .andExpect(jsonPath("$[?(@.internal == true)]", hasSize(0)));
    }

    @Test
    void assignedSupportSeesInternalNotes() throws Exception {
        getAs(SAM, "/api/accounts/1/notes").andExpect(status().isOk())
            .andExpect(jsonPath("$[?(@.internal == true)]", not(empty())));
    }

    @Test
    void anotherCustomerGets404() throws Exception {
        getAs(BOB, "/api/accounts/1/notes").andExpect(status().isNotFound());
    }
}
