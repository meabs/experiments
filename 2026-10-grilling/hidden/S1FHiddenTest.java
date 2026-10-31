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

/** Hidden tests for S1's follow-up (staff edit account notes). Not visible to the agent. */
class S1FHiddenTest extends ApiTest {

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

    private String body(long note) {
        return db().queryForObject("SELECT body FROM account_notes WHERE id = ?", String.class, note);
    }

    private boolean internal(long note) {
        return db().queryForObject("SELECT internal FROM account_notes WHERE id = ?", Boolean.class, note);
    }

    @Test
    void ticket_adminEditsBody() throws Exception {
        patchAs(ADA, "/api/accounts/1/notes/1", "{\"body\": \"  Welcome pack re-sent.  \"}").andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(1)).andExpect(jsonPath("$.body").value("Welcome pack re-sent."))
            .andExpect(jsonPath("$.internal").value(false));
        assertThat(body(1)).isEqualTo("Welcome pack re-sent.");
    }

    @Test
    void ticket_adminReclassifies() throws Exception {
        patchAs(ADA, "/api/accounts/1/notes/3", "{\"internal\": true}").andExpect(status().isOk())
            .andExpect(jsonPath("$.internal").value(true));
        assertThat(internal(3)).isTrue();
        assertThat(body(3)).isEqualTo("New debit card posted.");
    }

    @Test
    void ticket_assignedSupportEditsInternalNote() throws Exception {
        patchAs(SAM, "/api/accounts/1/notes/2", "{\"body\": \"Fraud alert; ID verified.\"}").andExpect(status().isOk());
        assertThat(body(2)).isEqualTo("Fraud alert; ID verified.");
    }

    @Test
    void ticket_invalidIs400() throws Exception {
        patchAs(ADA, "/api/accounts/1/notes/1", "{}").andExpect(status().isBadRequest());
        patchAs(ADA, "/api/accounts/1/notes/1", "{\"body\": \"  \"}").andExpect(status().isBadRequest());
        assertThat(body(1)).isEqualTo("Welcome pack sent.");
    }

    @Test
    void ticket_noteOnAnotherAccountIs404() throws Exception {
        patchAs(ADA, "/api/accounts/2/notes/1", "{\"body\": \"x\"}").andExpect(status().isNotFound());
        assertThat(body(1)).isEqualTo("Welcome pack sent.");
    }

    @Test
    void ra_supportCannotEditCustomerVisibleNote() throws Exception {
        patchAs(SAM, "/api/accounts/1/notes/3", "{\"body\": \"Changed\"}").andExpect(status().isForbidden());
        assertThat(body(3)).isEqualTo("New debit card posted.");
    }

    @Test
    void ra_supportCannotMakeNoteCustomerVisible() throws Exception {
        patchAs(SAM, "/api/accounts/1/notes/2", "{\"internal\": false}").andExpect(status().isForbidden());
        assertThat(internal(2)).isTrue();
    }

    @Test
    void rb_customerGets403() throws Exception {
        patchAs(ALICE, "/api/accounts/1/notes/1", "{\"body\": \"Changed\"}").andExpect(status().isForbidden());
        assertThat(body(1)).isEqualTo("Welcome pack sent.");
    }

    @Test
    void rb_unassignedSupportAndOtherBankGet404() throws Exception {
        patchAs(SUE, "/api/accounts/1/notes/2", "{\"body\": \"Changed\"}").andExpect(status().isNotFound());
        patchAs(GIL, "/api/accounts/1/notes/2", "{\"body\": \"Changed\"}").andExpect(status().isNotFound());
        assertThat(body(2)).startsWith("Fraud alert on card");
    }
}
