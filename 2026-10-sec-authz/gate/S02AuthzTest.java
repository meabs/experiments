package com.example.accounts.authz;

import static com.example.accounts.support.TestUsers.*;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

/** Security tests for PUT /api/customers/{customerId}/contact. */
class S02AuthzTest extends ApiTest {

    private static final String BODY = "{\"email\":\"alice.new@acme.test\",\"phone\":\"01632 960999\"}";

    @Test
    void customerUpdatesTheirOwnDetails() throws Exception {
        putAs(ALICE, "/api/customers/c-1/contact", BODY).andExpect(status().isOk())
            .andExpect(jsonPath("$.email").value("alice.new@acme.test"));
    }

    @Test
    void anotherCustomerGets404() throws Exception {
        putAs(BOB, "/api/customers/c-1/contact", BODY).andExpect(status().isNotFound());
    }

    @Test
    void supportGets403() throws Exception {
        putAs(SAM, "/api/customers/c-1/contact", BODY).andExpect(status().isForbidden());
    }

    @Test
    void writeScopeIsRequired() throws Exception {
        putWith(TestTokens.of(ALICE).scopes("accounts:read"), "/api/customers/c-1/contact", BODY)
            .andExpect(status().isForbidden());
    }
}
