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

/** Hidden tests for L2's follow-up (assign several cases at once). Not visible to the agent. */
class L2FHiddenTest extends ApiTest {

    private static final String ASSIGN = "/api/support/cases/assign";

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

    @Test
    void ticket_adminAssignsSeveral() throws Exception {
        postAs(ADA, ASSIGN, "{\"caseIds\": [\"k-3\", \"k-5\"], \"assigneeUserId\": \"u-ana\"}").andExpect(status().is2xxSuccessful())
            .andExpect(jsonPath("$[*].id", containsInAnyOrder("k-3", "k-5")))
            .andExpect(jsonPath("$[*].assigneeUserId", everyItem(is("u-ana"))))
            .andExpect(jsonPath("$[*].accountId", everyItem(is(3)))).andExpect(jsonPath("$[0].openedAt").exists());
        assertThat(assignee("k-3")).isEqualTo("u-ana");
        assertThat(assignee("k-5")).isEqualTo("u-ana");
    }

    @Test
    void ticket_noCaseIdsIs400() throws Exception {
        postAs(ADA, ASSIGN, "{\"caseIds\": [], \"assigneeUserId\": \"u-ana\"}").andExpect(status().isBadRequest());
    }

    @Test
    void ticket_adminsOnly() throws Exception {
        postAs(SUE, ASSIGN, "{\"caseIds\": [\"k-3\"], \"assigneeUserId\": \"u-ana\"}")
            .andExpect(status().is(anyOf(is(403), is(404))));
        postAs(BOB, ASSIGN, "{\"caseIds\": [\"k-3\"], \"assigneeUserId\": \"u-ana\"}")
            .andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(assignee("k-3")).isEqualTo("u-sue");
    }

    @Test
    void ra_assigneeMustBeAssignedToEveryCasesAccount() throws Exception {
        postAs(ADA, ASSIGN, "{\"caseIds\": [\"k-2\", \"k-3\"], \"assigneeUserId\": \"u-sam\"}")
            .andExpect(status().isBadRequest());
        assertThat(assignee("k-2")).isEqualTo("u-sue");
        assertThat(assignee("k-3")).isEqualTo("u-sue");
    }

    @Test
    void rb_unknownOrOtherBankCaseIs404AndNothingChanges() throws Exception {
        postAs(ADA, ASSIGN, "{\"caseIds\": [\"k-2\", \"k-4\"], \"assigneeUserId\": \"u-sam\"}")
            .andExpect(status().isNotFound());
        postAs(ADA, ASSIGN, "{\"caseIds\": [\"k-2\", \"k-999\"], \"assigneeUserId\": \"u-sam\"}")
            .andExpect(status().isNotFound());
        assertThat(assignee("k-2")).isEqualTo("u-sue");
        assertThat(assignee("k-4")).isEqualTo("u-gus");
    }

    @Test
    void rc_needsWriteScope() throws Exception {
        postWith(TestTokens.of(ADA).scopes("accounts:read"), ASSIGN,
            "{\"caseIds\": [\"k-3\"], \"assigneeUserId\": \"u-ana\"}").andExpect(status().isForbidden());
        assertThat(assignee("k-3")).isEqualTo("u-sue");
    }
}
