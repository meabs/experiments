package com.example.accounts.hidden;

import static com.example.accounts.support.TestUsers.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

/** Hidden tests for C1 (date filter on transactions). Not visible to the agent. */
class C1HiddenTest extends ApiTest {

    private static final TestTokens ADMIN = TestTokens.of(ADA).scopes("accounts:read transactions:read");
    private static final String T1 = "/api/accounts/1/transactions";

    @Test
    void ticket_noParametersUnchanged() throws Exception {
        getWith(ADMIN, T1).andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(2, 1)))
            .andExpect(jsonPath("$[0].amount").value(1850.0)).andExpect(jsonPath("$[0].bookedOn").value("2026-09-30"));
    }

    @Test
    void ticket_fromOnly() throws Exception {
        getWith(ADMIN, T1 + "?from=2026-09-29").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(2)));
    }

    @Test
    void ticket_toOnly() throws Exception {
        getWith(ADMIN, T1 + "?to=2026-09-28").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(1)));
    }

    @Test
    void ticket_bothInclusive() throws Exception {
        getWith(ADMIN, T1 + "?from=2026-09-28&to=2026-09-30").andExpect(status().isOk())
            .andExpect(jsonPath("$[*].id", contains(2, 1)));
        getWith(ADMIN, T1 + "?from=2026-09-30&to=2026-09-30").andExpect(status().isOk())
            .andExpect(jsonPath("$[*].id", contains(2)));
        getWith(ADMIN, T1 + "?from=2026-10-01").andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(0)));
    }

    @Test
    void ticket_invalidDateIs400() throws Exception {
        getWith(ADMIN, T1 + "?from=2026-13-01").andExpect(status().isBadRequest());
        getWith(ADMIN, T1 + "?to=yesterday").andExpect(status().isBadRequest());
    }

    @Test
    void ticket_fromAfterToIs400() throws Exception {
        getWith(ADMIN, T1 + "?from=2026-09-30&to=2026-09-28").andExpect(status().isBadRequest());
    }

    @Test
    void ticket_accessAndScopeUnchanged() throws Exception {
        getWith(TestTokens.of(ADA), T1 + "?from=2026-09-29").andExpect(status().isForbidden());
        getWith(TestTokens.of(BOB).scopes("accounts:read transactions:read"), T1 + "?from=2026-09-29")
            .andExpect(status().isNotFound());
        getWith(TestTokens.of(ALICE).scopes("accounts:read transactions:read"), T1 + "?to=2026-09-28")
            .andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(1)));
    }
}
