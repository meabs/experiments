package com.example.accounts.authz;

import static com.example.accounts.support.TestUsers.*;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

/** Security tests for GET /api/accounts/{accountId}/statements. */
class S06AuthzTest extends ApiTest {

    @Test
    void holderWithTheScopeSeesStatements() throws Exception {
        getWith(TestTokens.of(ALICE).scopes("accounts:read statements:read"), "/api/accounts/1/statements")
            .andExpect(status().isOk()).andExpect(jsonPath("$", not(empty())));
    }

    @Test
    void holderWithoutTheScopeGets403() throws Exception {
        getAs(ALICE, "/api/accounts/1/statements").andExpect(status().isForbidden());
    }

    @Test
    void anotherCustomerWithTheScopeGets404() throws Exception {
        getWith(TestTokens.of(BOB).scopes("accounts:read statements:read"), "/api/accounts/1/statements")
            .andExpect(status().isNotFound());
    }

    @Test
    void unauthenticatedIsRejected() throws Exception {
        getAnonymous("/api/accounts/1/statements").andExpect(status().isUnauthorized());
    }
}
