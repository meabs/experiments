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


/** Hidden evaluation tests for task S06 (not visible to the agent). Monthly statements. */
class S06HiddenTest extends ApiTest {

    private static final String A1 = "/api/accounts/1/statements";

    private static TestTokens withStatements(com.example.accounts.support.TestUsers.User u) {
        return TestTokens.of(u).scopes(u.scopes() + " statements:read");
    }

    @Test
    void functional_newestFirstWithBalances() throws Exception {
        getWith(withStatements(ALICE), A1).andExpect(status().isOk())
            .andExpect(jsonPath("$[*].period", contains("2026-09", "2026-08", "2026-07")))
            .andExpect(jsonPath("$[0].openingBalance").value(1100.0))
            .andExpect(jsonPath("$[0].closingBalance").value(1200.0));
    }

    @Test
    void functional_fromKeepsLaterPeriods() throws Exception {
        getWith(withStatements(ALICE), A1 + "?from=2026-08").andExpect(status().isOk())
            .andExpect(jsonPath("$[*].period", contains("2026-09", "2026-08")));
        getWith(withStatements(ALICE), A1 + "?from=2026-10").andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(0)));
    }

    @Test
    void functional_invalidFromGets400() throws Exception {
        getWith(withStatements(ALICE), A1 + "?from=2026-13").andExpect(status().isBadRequest());
        getWith(withStatements(ALICE), A1 + "?from=September").andExpect(status().isBadRequest());
        getWith(withStatements(ALICE), A1 + "?from=2026-9").andExpect(status().isBadRequest());
    }

    @Test
    void allows_holderAssignedSupportAndAdmin() throws Exception {
        getWith(withStatements(ALICE), "/api/accounts/2/statements").andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(1)));
        getWith(withStatements(SAM), "/api/accounts/2/statements").andExpect(status().isOk());
        getWith(withStatements(ADA), "/api/accounts/3/statements").andExpect(status().isOk());
        getWith(withStatements(GIL), "/api/accounts/4/statements").andExpect(status().isOk());
    }

    @Test
    void denies_withoutTheScopeGets403WhoeverTheCaller() throws Exception {
        getAs(ALICE, A1).andExpect(status().isForbidden());
        getAs(ADA, A1).andExpect(status().isForbidden());
        getAs(SAM, A1).andExpect(status().isForbidden());
    }

    @Test
    void denies_scopeIsCheckedBeforeTheAccount() throws Exception {
        getAs(BOB, A1).andExpect(status().isForbidden());
        getAs(ALICE, "/api/accounts/999/statements").andExpect(status().isForbidden());
    }

    @Test
    void denies_lookalikeScopes() throws Exception {
        for (String scope : List.of("statements", "statements:readonly", "statement:read", "statements:write",
                                    "accounts:read statements.read")) {
            getWith(TestTokens.of(ALICE).scopes(scope), A1).andExpect(status().isForbidden());
        }
    }

    @Test
    void denies_scopeNameInRolesIsNotAScope() throws Exception {
        getWith(TestTokens.of(ALICE).roles("CUSTOMER", "statements:read"), A1).andExpect(status().isForbidden());
    }

    @Test
    void denies_scopeDoesNotOpenOtherAccounts() throws Exception {
        getWith(withStatements(BOB), A1).andExpect(status().isNotFound());
        getWith(withStatements(SUE), A1).andExpect(status().isNotFound());
        getWith(withStatements(CAROL), A1).andExpect(status().isNotFound());
        getWith(withStatements(GIL), A1).andExpect(status().isNotFound());
        getWith(withStatements(ADA), "/api/accounts/4/statements").andExpect(status().isNotFound());
    }

    @Test
    void denies_missingAccountGets404() throws Exception {
        getWith(withStatements(ADA), "/api/accounts/999/statements").andExpect(status().isNotFound());
    }

    @Test
    void denies_unauthenticatedGets401() throws Exception {
        getAnonymous(A1).andExpect(status().isUnauthorized());
    }
}
