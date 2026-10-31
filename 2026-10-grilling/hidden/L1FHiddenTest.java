package com.example.accounts.hidden;

import static com.example.accounts.support.TestUsers.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;

import jakarta.persistence.EntityManager;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

/** Hidden tests for L1's follow-up (freeze all of a customer's accounts). Not visible to the agent. */
class L1FHiddenTest extends ApiTest {

    private static final String C1 = "/api/customers/c-1/freeze";
    private static final String WHY = "{\"reason\": \"Confirmed fraud\"}";

    @Autowired
    JdbcTemplate db;

    @Autowired
    EntityManager em;

    /** The database as the application left it: JPA's pending changes are written first. */
    private JdbcTemplate db() {
        em.flush();
        return db;
    }

    /** Changes fixture data directly, then makes JPA reload it. */
    private void sql(String statement, Object... args) {
        em.flush();
        db.update(statement, args);
        em.clear();
    }

    private String accountStatus(long id) {
        return db().queryForObject("SELECT status FROM accounts WHERE id = ?", String.class, id);
    }


    @Test
    void ticket_adminFreezesAllOfTheCustomersAccounts() throws Exception {
        postAs(ADA, C1, WHY).andExpect(status().is2xxSuccessful()).andExpect(jsonPath("$[*].id", containsInAnyOrder(1, 2)))
            .andExpect(jsonPath("$[*].status", everyItem(is("FROZEN"))));
        assertThat(accountStatus(1)).isEqualTo("FROZEN");
        assertThat(accountStatus(2)).isEqualTo("FROZEN");
        assertThat(accountStatus(3)).isEqualTo("OPEN");
    }

    @Test
    void ticket_invalidReasonIs400() throws Exception {
        postAs(ADA, C1, "{\"reason\": \"  \"}").andExpect(status().isBadRequest());
        assertThat(accountStatus(1)).isEqualTo("OPEN");
        assertThat(accountStatus(2)).isEqualTo("OPEN");
    }

    @Test
    void ticket_onlyAdminsOfTheBank() throws Exception {
        postAs(SAM, C1, WHY).andExpect(status().is(anyOf(is(403), is(404))));
        postAs(ALICE, C1, WHY).andExpect(status().is(anyOf(is(403), is(404))));
        postAs(GIL, C1, WHY).andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(accountStatus(1)).isEqualTo("OPEN");
        assertThat(accountStatus(2)).isEqualTo("OPEN");
    }

    @Test
    void ra_eachFrozenAccountGetsAnInternalNoteWithTheReason() throws Exception {
        postAs(ADA, C1, WHY).andExpect(status().is2xxSuccessful());
        for (long a : new long[] {1, 2}) {
            assertThat(db().queryForObject("SELECT COUNT(*) FROM account_notes WHERE account_id = ? AND internal = TRUE"
                + " AND author = 'u-ada' AND body LIKE '%Confirmed fraud%'", Integer.class, a)).isEqualTo(1);
        }
    }



    @Test
    void rb_needsWriteScope() throws Exception {
        postWith(TestTokens.of(ADA).scopes("accounts:read"), C1, WHY).andExpect(status().isForbidden());
        assertThat(accountStatus(1)).isEqualTo("OPEN");
        assertThat(accountStatus(2)).isEqualTo("OPEN");
    }
}
