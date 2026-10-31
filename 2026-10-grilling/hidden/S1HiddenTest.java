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

/** Hidden tests for S1 (staff add account notes). Not visible to the agent. */
class S1HiddenTest extends ApiTest {

    private static final String N1 = "/api/accounts/1/notes";

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

    private int notes(long account) {
        return db().queryForObject("SELECT COUNT(*) FROM account_notes WHERE account_id = ?", Integer.class, account);
    }

    @Test
    void ticket_adminAddsInternalNote() throws Exception {
        postAs(ADA, N1, "{\"body\": \"  Called the customer.  \", \"internal\": true}").andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").isNumber()).andExpect(jsonPath("$.author").value("u-ada"))
            .andExpect(jsonPath("$.body").value("Called the customer.")).andExpect(jsonPath("$.internal").value(true))
            .andExpect(jsonPath("$.createdAt").exists());
        assertThat(db().queryForObject("SELECT COUNT(*) FROM account_notes WHERE account_id = 1 AND author = 'u-ada'"
            + " AND body = 'Called the customer.' AND internal = TRUE", Integer.class)).isEqualTo(1);
    }

    @Test
    void ticket_adminAddsCustomerVisibleNote() throws Exception {
        postAs(ADA, N1, "{\"body\": \"Your new card is on its way.\", \"internal\": false}").andExpect(status().isCreated())
            .andExpect(jsonPath("$.internal").value(false));
    }

    @Test
    void ticket_assignedSupportAddsInternalNote() throws Exception {
        postAs(SAM, N1, "{\"body\": \"Checked ID.\", \"internal\": true}").andExpect(status().isCreated())
            .andExpect(jsonPath("$.author").value("u-sam"));
        postAs(ANA, "/api/accounts/3/notes", "{\"body\": \"Checked ID.\", \"internal\": true}")
            .andExpect(status().isCreated());
    }

    @Test
    void ticket_invalidBodyIs400() throws Exception {
        int before = notes(1);
        postAs(ADA, N1, "{\"body\": \"   \", \"internal\": true}").andExpect(status().isBadRequest());
        postAs(ADA, N1, "{\"body\": \"" + "x".repeat(2001) + "\", \"internal\": true}").andExpect(status().isBadRequest());
        postAs(ADA, N1, "{\"body\": \"Hello\"}").andExpect(status().isBadRequest());
        postAs(ADA, N1, "{\"internal\": true}").andExpect(status().isBadRequest());
        assertThat(notes(1)).isEqualTo(before);
    }

    @Test
    void ra_customerOwnerGets403() throws Exception {
        int before = notes(1);
        postAs(ALICE, N1, "{\"body\": \"Hi\", \"internal\": false}").andExpect(status().isForbidden());
        assertThat(notes(1)).isEqualTo(before);
    }

    @Test
    void ra_unassignedSupportAndOtherBankGet404() throws Exception {
        int before = notes(1);
        postAs(SUE, N1, "{\"body\": \"Hi\", \"internal\": true}").andExpect(status().isNotFound());
        postAs(GIL, N1, "{\"body\": \"Hi\", \"internal\": true}").andExpect(status().isNotFound());
        assertThat(notes(1)).isEqualTo(before);
    }

    @Test
    void rb_supportCannotAddCustomerVisibleNote() throws Exception {
        int before = notes(1);
        postAs(SAM, N1, "{\"body\": \"Your card is on its way.\", \"internal\": false}").andExpect(status().isForbidden());
        assertThat(notes(1)).isEqualTo(before);
    }
}
