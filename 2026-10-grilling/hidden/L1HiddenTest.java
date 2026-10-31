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

/** Hidden tests for L1 (freeze and unfreeze accounts). Not visible to the agent. */
class L1HiddenTest extends ApiTest {

    private static final String FREEZE = "/api/accounts/1/freeze";
    private static final String UNFREEZE = "/api/accounts/1/unfreeze";
    private static final String WHY = "{\"reason\": \"Suspicious card use\"}";

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

    private int internalNotesBy(String author) {
        return db().queryForObject("SELECT COUNT(*) FROM account_notes WHERE account_id = 1 AND internal = TRUE AND author = ?",
            Integer.class, author);
    }

    @Test
    void ticket_adminFreezesAndUnfreezes() throws Exception {
        postAs(ADA, FREEZE, WHY).andExpect(status().is2xxSuccessful()).andExpect(jsonPath("$.id").value(1))
            .andExpect(jsonPath("$.status").value("FROZEN")).andExpect(jsonPath("$.nickname").value("Everyday"));
        getAs(ADA, "/api/accounts/1").andExpect(status().isOk()).andExpect(jsonPath("$.status").value("FROZEN"));
        getAs(ALICE, "/api/accounts/1").andExpect(status().isOk()).andExpect(jsonPath("$.status").value("FROZEN"));
        postAs(ADA, UNFREEZE, null).andExpect(status().is2xxSuccessful()).andExpect(jsonPath("$.status").value("OPEN"));
        assertThat(accountStatus(1)).isEqualTo("OPEN");
    }

    @Test
    void ticket_customersCannotFreezeOrUnfreeze() throws Exception {
        postAs(ALICE, FREEZE, WHY).andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(accountStatus(1)).isEqualTo("OPEN");
        postAs(ADA, FREEZE, WHY).andExpect(status().is2xxSuccessful());
        postAs(ALICE, UNFREEZE, null).andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(accountStatus(1)).isEqualTo("FROZEN");
    }

    @Test
    void ticket_otherBankCannotFreeze() throws Exception {
        postAs(GIL, FREEZE, WHY).andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(accountStatus(1)).isEqualTo("OPEN");
    }

    @Test
    void ticket_invalidReasonIs400() throws Exception {
        postAs(ADA, FREEZE, "{\"reason\": \"   \"}").andExpect(status().isBadRequest());
        postAs(ADA, FREEZE, "{\"reason\": \"" + "x".repeat(501) + "\"}").andExpect(status().isBadRequest());
        assertThat(accountStatus(1)).isEqualTo("OPEN");
    }

    @Test
    void ra_freezeNeedsWriteScope() throws Exception {
        postWith(TestTokens.of(ADA).scopes("accounts:read"), FREEZE, WHY).andExpect(status().isForbidden());
        assertThat(accountStatus(1)).isEqualTo("OPEN");
    }

    @Test
    void ra_unfreezeNeedsWriteScope() throws Exception {
        postAs(ADA, FREEZE, WHY).andExpect(status().is2xxSuccessful());
        postWith(TestTokens.of(ADA).scopes("accounts:read"), UNFREEZE, null).andExpect(status().isForbidden());
        assertThat(accountStatus(1)).isEqualTo("FROZEN");
    }

    @Test
    void rb_freezingAClosedAccountIs409() throws Exception {
        postAs(ADA, "/api/accounts/5/freeze", WHY).andExpect(status().isConflict());
        assertThat(accountStatus(5)).isEqualTo("CLOSED");
    }

    @Test
    void rb_unfreezingAClosedAccountIs409() throws Exception {
        postAs(ADA, "/api/accounts/5/unfreeze", null).andExpect(status().isConflict());
        assertThat(accountStatus(5)).isEqualTo("CLOSED");
    }

    @Test
    void rc_assignedSupportCanFreeze() throws Exception {
        postAs(SAM, FREEZE, WHY).andExpect(status().is2xxSuccessful()).andExpect(jsonPath("$.status").value("FROZEN"));
        assertThat(accountStatus(1)).isEqualTo("FROZEN");
    }

    @Test
    void rc_supportCannotUnfreeze() throws Exception {
        postAs(ADA, FREEZE, WHY).andExpect(status().is2xxSuccessful());
        postAs(SAM, UNFREEZE, null).andExpect(status().isForbidden());
        assertThat(accountStatus(1)).isEqualTo("FROZEN");
    }

    @Test
    void rd_freezeAddsInternalNoteWithReason() throws Exception {
        postAs(ADA, FREEZE, WHY).andExpect(status().is2xxSuccessful());
        assertThat(db().queryForObject("SELECT COUNT(*) FROM account_notes WHERE account_id = 1 AND internal = TRUE"
            + " AND author = 'u-ada' AND body LIKE '%Suspicious card use%'", Integer.class)).isEqualTo(1);
    }

    @Test
    void rd_unfreezeAddsInternalNote() throws Exception {
        postAs(ADA, FREEZE, WHY).andExpect(status().is2xxSuccessful());
        int afterFreeze = internalNotesBy("u-ada");
        postAs(ADA, UNFREEZE, null).andExpect(status().is2xxSuccessful());
        assertThat(internalNotesBy("u-ada")).isEqualTo(afterFreeze + 1);
    }
}
