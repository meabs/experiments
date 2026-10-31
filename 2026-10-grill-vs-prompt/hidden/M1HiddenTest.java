package com.example.accounts.hidden;

import static com.example.accounts.support.TestUsers.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.math.BigDecimal;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;

import jakarta.persistence.EntityManager;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

/** Hidden tests for M1 (change an account's daily limit). Not visible to the agent. */
class M1HiddenTest extends ApiTest {

    private static final String URL = "/api/accounts/1/daily-limit";

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

    private BigDecimal balance(long id) {
        return db().queryForObject("SELECT balance FROM accounts WHERE id = ?", BigDecimal.class, id);
    }

    private String accountStatus(long id) {
        return db().queryForObject("SELECT status FROM accounts WHERE id = ?", String.class, id);
    }

    private int transactions(long account, String description) {
        return db().queryForObject("SELECT COUNT(*) FROM transactions WHERE account_id = ? AND description = ?",
            Integer.class, account, description);
    }

    private int limit(long id) {
        return db().queryForObject("SELECT daily_limit FROM accounts WHERE id = ?", Integer.class, id);
    }

    private static String body(int n) {
        return "{\"dailyLimit\": " + n + "}";
    }

    @Test
    void ticket_adminSetsTheLimit() throws Exception {
        putAs(ADA, URL, body(300)).andExpect(status().is2xxSuccessful()).andExpect(jsonPath("$.id").value(1))
            .andExpect(jsonPath("$.dailyLimit").value(300)).andExpect(jsonPath("$.nickname").value("Everyday"));
        getAs(ADA, "/api/accounts/1").andExpect(status().isOk()).andExpect(jsonPath("$.dailyLimit").value(300));
        assertThat(limit(1)).isEqualTo(300);
    }

    @Test
    void ticket_customersCannotChangeIt() throws Exception {
        putAs(ALICE, URL, body(300)).andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(limit(1)).isEqualTo(500);
    }

    @Test
    void ticket_otherBankCannotChangeIt() throws Exception {
        putAs(GIL, URL, body(300)).andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(limit(1)).isEqualTo(500);
    }

    @Test
    void ticket_invalidLimitIs400() throws Exception {
        putAs(ADA, URL, body(-1)).andExpect(status().isBadRequest());
        putAs(ADA, URL, "{\"dailyLimit\": \"lots\"}").andExpect(status().isBadRequest());
        putAs(ADA, URL, "{}").andExpect(status().isBadRequest());
        assertThat(limit(1)).isEqualTo(500);
    }

    @Test
    void ra_needsWriteScope() throws Exception {
        putWith(TestTokens.of(ADA).scopes("accounts:read"), URL, body(300)).andExpect(status().isForbidden());
        assertThat(limit(1)).isEqualTo(500);
    }

    @Test
    void rb_closedAccountIs409() throws Exception {
        putAs(ADA, "/api/accounts/5/daily-limit", body(100)).andExpect(status().isConflict());
        assertThat(limit(5)).isEqualTo(0);
    }

    @Test
    void rc_assignedSupportCanLowerIt() throws Exception {
        putAs(SAM, URL, body(200)).andExpect(status().is2xxSuccessful());
        assertThat(limit(1)).isEqualTo(200);
    }

    @Test
    void rc_supportCannotRaiseIt() throws Exception {
        putAs(SAM, URL, body(800)).andExpect(status().isForbidden());
        assertThat(limit(1)).isEqualTo(500);
    }

    @Test
    void rc_adminCanRaiseIt() throws Exception {
        putAs(ADA, URL, body(800)).andExpect(status().is2xxSuccessful());
        assertThat(limit(1)).isEqualTo(800);
    }

    @Test
    void rd_ceilingIs5000() throws Exception {
        putAs(ADA, URL, body(5001)).andExpect(status().isBadRequest());
        assertThat(limit(1)).isEqualTo(500);
        putAs(ADA, URL, body(5000)).andExpect(status().is2xxSuccessful());
        assertThat(limit(1)).isEqualTo(5000);
    }

    @Test
    void re_savingsLimitIsFixed() throws Exception {
        putAs(ADA, "/api/accounts/2/daily-limit", body(100)).andExpect(status().isConflict());
        assertThat(limit(2)).isEqualTo(250);
    }

    @Test
    void rf_changeAddsInternalNoteWithOldAndNew() throws Exception {
        putAs(SAM, URL, body(200)).andExpect(status().is2xxSuccessful());
        assertThat(db().queryForObject("SELECT COUNT(*) FROM account_notes WHERE account_id = 1 AND internal = TRUE"
            + " AND author = 'u-sam' AND body LIKE '%500%' AND body LIKE '%200%'", Integer.class)).isEqualTo(1);
    }
}
