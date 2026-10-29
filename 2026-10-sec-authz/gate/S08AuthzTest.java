package com.example.accounts.authz;

import static com.example.accounts.support.TestUsers.*;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

/** Security tests for PATCH /api/accounts/{accountId}. */
class S08AuthzTest extends ApiTest {

    @Test
    void holderRenamesTheirAccount() throws Exception {
        patchAs(ALICE, "/api/accounts/1", "{\"nickname\":\"Bills\"}").andExpect(status().isOk())
            .andExpect(jsonPath("$.nickname").value("Bills"));
    }

    @Test
    void holderCannotChangeTheDailyLimit() throws Exception {
        patchAs(ALICE, "/api/accounts/1", "{\"dailyLimit\":5000}").andExpect(status().isForbidden());
    }

    @Test
    void adminChangesTheDailyLimit() throws Exception {
        patchAs(ADA, "/api/accounts/1", "{\"dailyLimit\":1000}").andExpect(status().isOk())
            .andExpect(jsonPath("$.dailyLimit").value(1000));
    }

    @Test
    void anotherCustomerGets404() throws Exception {
        patchAs(BOB, "/api/accounts/1", "{\"nickname\":\"Mine\"}").andExpect(status().isNotFound());
    }
}
