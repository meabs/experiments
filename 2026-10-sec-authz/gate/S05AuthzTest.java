package com.example.accounts.authz;

import static com.example.accounts.support.TestUsers.*;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

/** Security tests for GET /api/support/cases/{caseId}. */
class S05AuthzTest extends ApiTest {

    @Test
    void assigneeSeesTheCaseWithInternalComments() throws Exception {
        getAs(SUE, "/api/support/cases/k-2").andExpect(status().isOk())
            .andExpect(jsonPath("$.comments[?(@.internal == true)]", not(empty())));
    }

    @Test
    void customerGets403() throws Exception {
        getAs(ALICE, "/api/support/cases/k-1").andExpect(status().isForbidden());
    }

    @Test
    void supportUserNotAssignedToTheCaseGets404() throws Exception {
        getAs(SAM, "/api/support/cases/k-3").andExpect(status().isNotFound());
    }

    @Test
    void unauthenticatedIsRejected() throws Exception {
        getAnonymous("/api/support/cases/k-1").andExpect(status().isUnauthorized());
    }
}
