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

/** Hidden tests for L2 (reassign support cases). Not visible to the agent. */
class L2HiddenTest extends ApiTest {

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

    private String assignee(String id) {
        return db().queryForObject("SELECT assignee_user_id FROM support_cases WHERE id = ?", String.class, id);
    }

    private static String to(String user) {
        return "{\"assigneeUserId\": \"" + user + "\"}";
    }

    @Test
    void ticket_adminReassigns() throws Exception {
        putAs(ADA, "/api/support/cases/k-3/assignee", to("u-ana")).andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value("k-3")).andExpect(jsonPath("$.accountId").value(3))
            .andExpect(jsonPath("$.subject").value("Change of address")).andExpect(jsonPath("$.status").value("OPEN"))
            .andExpect(jsonPath("$.assigneeUserId").value("u-ana")).andExpect(jsonPath("$.openedAt").exists());
        assertThat(assignee("k-3")).isEqualTo("u-ana");
        putAs(ADA, "/api/support/cases/k-2/assignee", to("u-sam")).andExpect(status().isOk());
        assertThat(assignee("k-2")).isEqualTo("u-sam");
    }

    @Test
    void ticket_customersCannotReassign() throws Exception {
        putAs(BOB, "/api/support/cases/k-3/assignee", to("u-ana")).andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(assignee("k-3")).isEqualTo("u-sue");
    }

    @Test
    void ra_needsWriteScope() throws Exception {
        putWith(TestTokens.of(ADA).scopes("accounts:read"), "/api/support/cases/k-3/assignee", to("u-ana"))
            .andExpect(status().isForbidden());
        assertThat(assignee("k-3")).isEqualTo("u-sue");
    }

    @Test
    void rb_caseInAnotherBankIs404() throws Exception {
        putAs(ADA, "/api/support/cases/k-4/assignee", to("u-sam")).andExpect(status().isNotFound());
        putAs(GIL, "/api/support/cases/k-1/assignee", to("u-gus")).andExpect(status().isNotFound());
        assertThat(assignee("k-4")).isEqualTo("u-gus");
        assertThat(assignee("k-1")).isEqualTo("u-sam");
    }

    @Test
    void rc_newAssigneeMustBeAssignedToTheAccount() throws Exception {
        putAs(ADA, "/api/support/cases/k-1/assignee", to("u-sue")).andExpect(status().isBadRequest());
        putAs(ADA, "/api/support/cases/k-3/assignee", to("u-nobody")).andExpect(status().isBadRequest());
        putAs(ADA, "/api/support/cases/k-3/assignee", to("u-gus")).andExpect(status().isBadRequest());
        assertThat(assignee("k-1")).isEqualTo("u-sam");
        assertThat(assignee("k-3")).isEqualTo("u-sue");
    }

    @Test
    void rd_currentAssigneeCanHandOver() throws Exception {
        putAs(SUE, "/api/support/cases/k-3/assignee", to("u-ana")).andExpect(status().isOk())
            .andExpect(jsonPath("$.assigneeUserId").value("u-ana"));
        assertThat(assignee("k-3")).isEqualTo("u-ana");
    }

    @Test
    void rd_otherSupportUsersCannot() throws Exception {
        putAs(ANA, "/api/support/cases/k-3/assignee", to("u-ana")).andExpect(status().is(anyOf(is(403), is(404))));
        putAs(SAM, "/api/support/cases/k-3/assignee", to("u-ana")).andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(assignee("k-3")).isEqualTo("u-sue");
    }
}
