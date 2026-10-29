package com.example.accounts;

import static com.example.accounts.support.TestUsers.*;
import static org.hamcrest.Matchers.containsInAnyOrder;
import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.Instant;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

class AccountApiTest extends ApiTest {

    @Test
    void ownerSeesTheirAccount() throws Exception {
        getAs(ALICE, "/api/accounts/1").andExpect(status().isOk()).andExpect(jsonPath("$.nickname").value("Everyday"));
    }

    @Test
    void customerListsOnlyTheirAccounts() throws Exception {
        getAs(ALICE, "/api/accounts").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", containsInAnyOrder(1, 2)));
    }

    @Test
    void anotherCustomersAccountIsNotFound() throws Exception {
        getAs(BOB, "/api/accounts/1").andExpect(status().isNotFound());
    }

    @Test
    void accountInAnotherTenantIsNotFoundEvenForAdmins() throws Exception {
        getAs(GIL, "/api/accounts/1").andExpect(status().isNotFound());
        getAs(ADA, "/api/accounts/4").andExpect(status().isNotFound());
    }

    @Test
    void supportSeesOnlyAssignedAccounts() throws Exception {
        getAs(SAM, "/api/accounts/1").andExpect(status().isOk());
        getAs(SAM, "/api/accounts/3").andExpect(status().isNotFound());
        getAs(SAM, "/api/accounts").andExpect(jsonPath("$[*].id", containsInAnyOrder(1, 2)));
    }

    @Test
    void adminSeesEveryAccountInTheirTenant() throws Exception {
        getAs(ADA, "/api/accounts").andExpect(jsonPath("$", hasSize(4)));
    }

    @Test
    void unauthenticatedCallsAreRejected() throws Exception {
        getAnonymous("/api/accounts/1").andExpect(status().isUnauthorized());
    }

    @Test
    void expiredTokenIsRejected() throws Exception {
        getWith(TestTokens.of(ALICE).expiredAt(Instant.now().minusSeconds(600)), "/api/accounts/1")
            .andExpect(status().isUnauthorized());
    }

    @Test
    void transactionsNeedTheTransactionsScope() throws Exception {
        getAs(ALICE, "/api/accounts/1/transactions").andExpect(status().isForbidden());
        getWith(TestTokens.of(ALICE).scopes("accounts:read transactions:read"), "/api/accounts/1/transactions")
            .andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(2)));
    }

    @Test
    void transactionsScopeDoesNotOpenOtherAccounts() throws Exception {
        getWith(TestTokens.of(BOB).scopes("transactions:read"), "/api/accounts/1/transactions")
            .andExpect(status().isNotFound());
    }
}
