package com.example.accounts.hidden;

import static com.example.accounts.support.TestUsers.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

/** Hidden tests for C2 (status filter on the account list). Not visible to the agent. */
class C2HiddenTest extends ApiTest {

    @Test
    void ticket_noParameterUnchanged() throws Exception {
        getAs(ADA, "/api/accounts").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(1, 2, 3, 5)));
    }

    @Test
    void ticket_closed() throws Exception {
        getAs(ADA, "/api/accounts?status=CLOSED").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(5)))
            .andExpect(jsonPath("$[0].status").value("CLOSED"));
    }

    @Test
    void ticket_open() throws Exception {
        getAs(ADA, "/api/accounts?status=OPEN").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(1, 2, 3)));
    }

    @Test
    void ticket_otherValuesAre400() throws Exception {
        getAs(ADA, "/api/accounts?status=open").andExpect(status().isBadRequest());
        getAs(ADA, "/api/accounts?status=FROZEN").andExpect(status().isBadRequest());
    }

    @Test
    void ticket_visibilityUnchanged() throws Exception {
        getAs(SAM, "/api/accounts?status=OPEN").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(1, 2)));
        getAs(ALICE, "/api/accounts?status=CLOSED").andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(0)));
        getAs(DANA, "/api/accounts?status=CLOSED").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(5)));
        getAs(GIL, "/api/accounts?status=OPEN").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", contains(4)));
    }
}
