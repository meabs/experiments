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

/** Hidden tests for S2's follow-up (staff reopen closed cases). Not visible to the agent. */
class S2FHiddenTest extends ApiTest {

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

    private String caseStatus(String id) {
        return db().queryForObject("SELECT status FROM support_cases WHERE id = ?", String.class, id);
    }

    private void closeAsAdmin(String id) {
        sql("UPDATE support_cases SET status = 'CLOSED' WHERE id = ?", id);
    }

    private static String reason(String text) {
        return "{\"reason\": \"" + text + "\"}";
    }

    @Test
    void ticket_assigneeReopens() throws Exception {
        closeAsAdmin("k-1");
        postAs(SAM, "/api/support/cases/k-1/reopen", reason("Card still missing.")).andExpect(status().is2xxSuccessful())
            .andExpect(jsonPath("$.id").value("k-1")).andExpect(jsonPath("$.status").value("OPEN"));
        assertThat(caseStatus("k-1")).isEqualTo("OPEN");
        assertThat(db().queryForObject("SELECT assignee_user_id FROM support_cases WHERE id = 'k-1'", String.class))
            .isEqualTo("u-sam");
    }

    @Test
    void ticket_adminReopens() throws Exception {
        closeAsAdmin("k-3");
        postAs(ADA, "/api/support/cases/k-3/reopen", reason("Wrong address again.")).andExpect(status().is2xxSuccessful())
            .andExpect(jsonPath("$.status").value("OPEN"));
    }

    @Test
    void ticket_invalidReasonIs400() throws Exception {
        closeAsAdmin("k-1");
        postAs(SAM, "/api/support/cases/k-1/reopen", reason("  ")).andExpect(status().isBadRequest());
        assertThat(caseStatus("k-1")).isEqualTo("CLOSED");
    }

    @Test
    void ticket_othersCannotReopen() throws Exception {
        closeAsAdmin("k-1");
        postAs(SUE, "/api/support/cases/k-1/reopen", reason("x")).andExpect(status().is(anyOf(is(403), is(404))));
        postAs(ALICE, "/api/support/cases/k-1/reopen", reason("x")).andExpect(status().is(anyOf(is(403), is(404))));
        postAs(GIL, "/api/support/cases/k-1/reopen", reason("x")).andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(caseStatus("k-1")).isEqualTo("CLOSED");
    }

    @Test
    void ra_reasonIsACommentTheCustomerCanSee() throws Exception {
        closeAsAdmin("k-1");
        postAs(SAM, "/api/support/cases/k-1/reopen", reason("Card still missing.")).andExpect(status().is2xxSuccessful());
        assertThat(db().queryForObject("SELECT COUNT(*) FROM case_comments WHERE case_id = 'k-1' AND author = 'u-sam'"
            + " AND internal = FALSE AND body LIKE '%Card still missing.%'", Integer.class)).isEqualTo(1);
    }

    @Test
    void rb_reopeningAnOpenCaseIs409() throws Exception {
        postAs(SAM, "/api/support/cases/k-1/reopen", reason("x")).andExpect(status().isConflict());
        assertThat(caseStatus("k-1")).isEqualTo("OPEN");
    }
}
