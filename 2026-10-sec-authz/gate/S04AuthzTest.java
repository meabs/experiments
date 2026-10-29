package com.example.accounts.authz;

import static com.example.accounts.support.TestUsers.*;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

/** Security tests for GET /api/customers/search. */
class S04AuthzTest extends ApiTest {

    @Test
    void adminFindsCustomers() throws Exception {
        getAs(ADA, "/api/customers/search?q=brown").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains("c-2")));
    }

    @Test
    void customerGets403() throws Exception {
        getAs(ALICE, "/api/customers/search?q=brown").andExpect(status().isForbidden());
    }

    @Test
    void resultsHaveNoRiskScore() throws Exception {
        getAs(ADA, "/api/customers/search?q=brown").andExpect(jsonPath("$[0].riskScore").doesNotExist());
    }

    @Test
    void unauthenticatedIsRejected() throws Exception {
        getAnonymous("/api/customers/search?q=brown").andExpect(status().isUnauthorized());
    }
}
