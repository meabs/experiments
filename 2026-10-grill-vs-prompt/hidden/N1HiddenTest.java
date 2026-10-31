package com.example.accounts.hidden;

import static com.example.accounts.support.TestUsers.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.math.BigDecimal;

import org.junit.jupiter.api.Test;
import com.jayway.jsonpath.JsonPath;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;

import jakarta.persistence.EntityManager;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

/** Hidden tests for N1 (goodwill credits). Not visible to the agent. */
class N1HiddenTest extends ApiTest {

    private static final String URL = "/api/accounts/1/goodwill-credits";

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

    private static String credit(String amount) {
        return "{\"amount\": " + amount + ", \"reason\": \"Card lost in the post twice\"}";
    }

    private long create(com.example.accounts.support.TestUsers.User who, long account, String amount) throws Exception {
        String json = postAs(who, "/api/accounts/" + account + "/goodwill-credits", credit(amount))
            .andExpect(status().isCreated()).andReturn().getResponse().getContentAsString();
        return ((Number) JsonPath.read(json, "$.id")).longValue();
    }

    private String approve(long id) {
        return "/api/goodwill-credits/" + id + "/approve";
    }

    @Test
    void ticket_adminGivesASmallCredit() throws Exception {
        postAs(ADA, URL, credit("25.00")).andExpect(status().isCreated()).andExpect(jsonPath("$.id").exists())
            .andExpect(jsonPath("$.accountId").value(1)).andExpect(jsonPath("$.amount").value(25.0))
            .andExpect(jsonPath("$.reason").value("Card lost in the post twice"))
            .andExpect(jsonPath("$.createdBy").value("u-ada")).andExpect(jsonPath("$.createdAt").exists());
        assertThat(balance(1)).isEqualByComparingTo("1225.00");
        assertThat(transactions(1, "Goodwill credit")).isEqualTo(1);
    }

    @Test
    void ticket_assignedSupportGivesACredit() throws Exception {
        postAs(SAM, URL, credit("10.50")).andExpect(status().isCreated());
        assertThat(balance(1)).isEqualByComparingTo("1210.50");
    }

    @Test
    void ticket_customersCannotGiveCredits() throws Exception {
        postAs(ALICE, URL, credit("25.00")).andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(balance(1)).isEqualByComparingTo("1200.00");
    }

    @Test
    void ticket_otherBankCannotGiveCredits() throws Exception {
        postAs(GIL, URL, credit("25.00")).andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(balance(1)).isEqualByComparingTo("1200.00");
    }

    @Test
    void ticket_invalidCreditIs400() throws Exception {
        postAs(ADA, URL, credit("0")).andExpect(status().isBadRequest());
        postAs(ADA, URL, credit("-5")).andExpect(status().isBadRequest());
        postAs(ADA, URL, credit("1.234")).andExpect(status().isBadRequest());
        postAs(ADA, URL, "{\"amount\": 5, \"reason\": \"   \"}").andExpect(status().isBadRequest());
        assertThat(balance(1)).isEqualByComparingTo("1200.00");
        assertThat(transactions(1, "Goodwill credit")).isZero();
    }

    @Test
    void ra_needsWriteScope() throws Exception {
        postWith(TestTokens.of(ADA).scopes("accounts:read"), URL, credit("25.00")).andExpect(status().isForbidden());
        assertThat(balance(1)).isEqualByComparingTo("1200.00");
    }

    @Test
    void rb_over100WaitsAndIsNotPaid() throws Exception {
        postAs(ADA, URL, credit("150.00")).andExpect(status().isCreated());
        assertThat(balance(1)).isEqualByComparingTo("1200.00");
        assertThat(transactions(1, "Goodwill credit")).isZero();
        postAs(ADA, URL, credit("100.00")).andExpect(status().isCreated());
        assertThat(balance(1)).isEqualByComparingTo("1300.00");
    }

    @Test
    void rc_approverApprovesAndItIsPaid() throws Exception {
        long id = create(ADA, 1, "150.00");
        postAs(AL, approve(id), null).andExpect(status().is2xxSuccessful());
        assertThat(balance(1)).isEqualByComparingTo("1350.00");
        assertThat(transactions(1, "Goodwill credit")).isEqualTo(1);
    }

    @Test
    void rc_approvingTwiceIs409() throws Exception {
        long id = create(ADA, 1, "150.00");
        postAs(AL, approve(id), null).andExpect(status().is2xxSuccessful());
        postAs(AL, approve(id), null).andExpect(status().isConflict());
        assertThat(balance(1)).isEqualByComparingTo("1350.00");
    }

    @Test
    void rc_nonApproversCannotApprove() throws Exception {
        long id = create(ADA, 1, "150.00");
        postAs(SAM, approve(id), null).andExpect(status().is(anyOf(is(403), is(404))));
        postAs(ADA, approve(id), null).andExpect(status().is(anyOf(is(403), is(404))));
        postAs(GWEN, approve(id), null).andExpect(status().isNotFound());
        assertThat(balance(1)).isEqualByComparingTo("1200.00");
    }

    @Test
    void rd_cannotApproveYourOwnCredit() throws Exception {
        long id = create(ANA, 3, "150.00");
        postAs(ANA, approve(id), null).andExpect(status().isForbidden());
        assertThat(balance(3)).isEqualByComparingTo("300.00");
        postAs(AL, approve(id), null).andExpect(status().is2xxSuccessful());
        assertThat(balance(3)).isEqualByComparingTo("450.00");
    }
}
