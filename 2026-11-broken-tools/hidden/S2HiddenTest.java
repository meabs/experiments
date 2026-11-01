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

/** Hidden tests for S2 (staff close support cases). Not visible to the agent. */
class S2HiddenTest extends ApiTest {

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

    private int comments(String id) {
        return db().queryForObject("SELECT COUNT(*) FROM case_comments WHERE case_id = ?", Integer.class, id);
    }

    private static String close(String text) {
        return "{\"resolution\": \"" + text + "\"}";
    }

    @Test
    void ticket_assigneeCloses() throws Exception {
        postAs(SAM, "/api/support/cases/k-1/close", close("  Card delivered.  ")).andExpect(status().is2xxSuccessful())
            .andExpect(jsonPath("$.id").value("k-1")).andExpect(jsonPath("$.accountId").value(1))
            .andExpect(jsonPath("$.subject").value("Card not arrived")).andExpect(jsonPath("$.status").value("CLOSED"))
            .andExpect(jsonPath("$.openedAt").exists());
        assertThat(caseStatus("k-1")).isEqualTo("CLOSED");
    }

    @Test
    void ticket_adminCloses() throws Exception {
        postAs(ADA, "/api/support/cases/k-3/close", close("Address updated.")).andExpect(status().is2xxSuccessful())
            .andExpect(jsonPath("$.status").value("CLOSED"));
        assertThat(caseStatus("k-3")).isEqualTo("CLOSED");
    }

    @Test
    void ticket_invalidResolutionIs400() throws Exception {
        postAs(SAM, "/api/support/cases/k-1/close", close("   ")).andExpect(status().isBadRequest());
        postAs(SAM, "/api/support/cases/k-1/close", close("x".repeat(2001))).andExpect(status().isBadRequest());
        assertThat(caseStatus("k-1")).isEqualTo("OPEN");
    }

    @Test
    void ticket_othersCannotClose() throws Exception {
        postAs(SUE, "/api/support/cases/k-1/close", close("Done")).andExpect(status().is(anyOf(is(403), is(404))));
        postAs(ALICE, "/api/support/cases/k-1/close", close("Done")).andExpect(status().is(anyOf(is(403), is(404))));
        postAs(GIL, "/api/support/cases/k-1/close", close("Done")).andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(caseStatus("k-1")).isEqualTo("OPEN");
    }

    @Test
    void ra_closingAClosedCaseIs409() throws Exception {
        postAs(ADA, "/api/support/cases/k-3/close", close("Address updated.")).andExpect(status().is2xxSuccessful());
        int after = comments("k-3");
        postAs(ADA, "/api/support/cases/k-3/close", close("Again.")).andExpect(status().isConflict());
        assertThat(caseStatus("k-3")).isEqualTo("CLOSED");
        assertThat(comments("k-3")).isEqualTo(after);
    }

    @Test
    void rb_resolutionIsACommentTheCustomerCanSee() throws Exception {
        postAs(SAM, "/api/support/cases/k-1/close", close("Card delivered by courier.")).andExpect(status().is2xxSuccessful());
        assertThat(db().queryForObject("SELECT COUNT(*) FROM case_comments WHERE case_id = 'k-1' AND author = 'u-sam'"
            + " AND internal = FALSE AND body LIKE '%Card delivered by courier.%'", Integer.class)).isEqualTo(1);
    }
}
