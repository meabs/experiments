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

/** Hidden tests for N2 (approve closure requests). Not visible to the agent. */
class N2HiddenTest extends ApiTest {

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

    private String requestStatus(long id) {
        return db().queryForObject("SELECT status FROM closure_requests WHERE id = ?", String.class, id);
    }

    private int transactionsOf(long account, String amount) {
        return db().queryForObject("SELECT COUNT(*) FROM transactions WHERE account_id = ? AND amount = ?",
            Integer.class, account, new BigDecimal(amount));
    }

    private static String approve(long id) {
        return "/api/closure-requests/" + id + "/approve";
    }

    private static String to(long account) {
        return "{\"transferToAccountId\": " + account + "}";
    }

    private void emptyAccount3() {
        sql("UPDATE accounts SET balance = 0 WHERE id = 3");
    }

    @Test
    void ticket_approverApprovesAnEmptyAccount() throws Exception {
        emptyAccount3();
        postAs(ANA, approve(2), null).andExpect(status().is2xxSuccessful()).andExpect(jsonPath("$.id").value(2))
            .andExpect(jsonPath("$.accountId").value(3)).andExpect(jsonPath("$.status").value("APPROVED"))
            .andExpect(jsonPath("$.decidedBy").value("u-ana"));
        assertThat(requestStatus(2)).isEqualTo("APPROVED");
        assertThat(accountStatus(3)).isEqualTo("CLOSED");
        assertThat(db().queryForObject("SELECT decided_at FROM closure_requests WHERE id = 2", Object.class)).isNotNull();
    }

    @Test
    void ticket_nonApproversCannotApprove() throws Exception {
        emptyAccount3();
        postAs(ADA, approve(2), null).andExpect(status().is(anyOf(is(403), is(404))));
        postAs(SUE, approve(2), null).andExpect(status().is(anyOf(is(403), is(404))));
        postAs(BOB, approve(2), null).andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(requestStatus(2)).isEqualTo("PENDING");
        assertThat(accountStatus(3)).isEqualTo("OPEN");
    }

    @Test
    void ticket_otherBankCannotApprove() throws Exception {
        emptyAccount3();
        postAs(GWEN, approve(2), null).andExpect(status().is(anyOf(is(403), is(404))));
        assertThat(requestStatus(2)).isEqualTo("PENDING");
    }

    @Test
    void ra_needsWriteScope() throws Exception {
        emptyAccount3();
        postWith(TestTokens.of(ANA).scopes("accounts:read"), approve(2), null).andExpect(status().isForbidden());
        assertThat(requestStatus(2)).isEqualTo("PENDING");
    }

    @Test
    void rb_onlyPendingRequests() throws Exception {
        postAs(ANA, approve(3), null).andExpect(status().isConflict());
        assertThat(requestStatus(3)).isEqualTo("APPROVED");
        emptyAccount3();
        sql("UPDATE closure_requests SET status = 'REJECTED' WHERE id = 2");
        postAs(ANA, approve(2), null).andExpect(status().isConflict());
        assertThat(requestStatus(2)).isEqualTo("REJECTED");
        assertThat(accountStatus(3)).isEqualTo("OPEN");
    }

    @Test
    void rc_moneyInTheAccountNeedsATransferAccount() throws Exception {
        postAs(ANA, approve(1), null).andExpect(status().isConflict());
        postAs(ANA, approve(1), "{}").andExpect(status().isConflict());
        assertThat(requestStatus(1)).isEqualTo("PENDING");
        assertThat(accountStatus(2)).isEqualTo("OPEN");
        assertThat(balance(2)).isEqualByComparingTo("8000.00");
    }

    @Test
    void rc_transferMovesTheMoneyAndCloses() throws Exception {
        postAs(ANA, approve(1), to(1)).andExpect(status().is2xxSuccessful());
        assertThat(requestStatus(1)).isEqualTo("APPROVED");
        assertThat(accountStatus(2)).isEqualTo("CLOSED");
        assertThat(balance(2)).isEqualByComparingTo("0");
        assertThat(balance(1)).isEqualByComparingTo("9200.00");
    }

    @Test
    void rd_transferMustGoToAnotherOpenAccountOfTheSameCustomer() throws Exception {
        for (long bad : new long[] {3, 4, 5, 2, 999}) {
            postAs(ANA, approve(1), to(bad)).andExpect(status().is(allOf(greaterThanOrEqualTo(400), lessThan(500))));
        }
        sql("UPDATE accounts SET status = 'CLOSED' WHERE id = 1");
        postAs(ANA, approve(1), to(1)).andExpect(status().is(allOf(greaterThanOrEqualTo(400), lessThan(500))));
        assertThat(requestStatus(1)).isEqualTo("PENDING");
        assertThat(accountStatus(2)).isEqualTo("OPEN");
        assertThat(balance(2)).isEqualByComparingTo("8000.00");
    }

    @Test
    void re_theMoveIsBookedOnBothAccounts() throws Exception {
        postAs(ANA, approve(1), to(1)).andExpect(status().is2xxSuccessful());
        assertThat(transactionsOf(2, "-8000.00")).isEqualTo(1);
        assertThat(transactionsOf(1, "8000.00")).isEqualTo(1);
    }
}
