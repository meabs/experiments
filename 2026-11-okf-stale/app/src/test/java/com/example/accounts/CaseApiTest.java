package com.example.accounts;

import static com.example.accounts.support.TestUsers.*;
import static org.hamcrest.Matchers.containsInAnyOrder;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;

class CaseApiTest extends ApiTest {

    @Test
    void customerSeesCasesTheyRaised() throws Exception {
        getAs(ALICE, "/api/cases").andExpect(jsonPath("$[*].id", containsInAnyOrder("k-1", "k-2")));
    }

    @Test
    void supportSeesCasesAssignedToThem() throws Exception {
        getAs(SUE, "/api/cases").andExpect(jsonPath("$[*].id", containsInAnyOrder("k-2", "k-3")));
    }

    @Test
    void adminSeesTheTenantsCases() throws Exception {
        getAs(ADA, "/api/cases").andExpect(jsonPath("$[*].id", containsInAnyOrder("k-1", "k-2", "k-3", "k-5")));
    }

    @Test
    void customerRaisesACaseOnTheirAccount() throws Exception {
        postAs(BOB, "/api/cases", "{\"accountId\":3,\"subject\":\"Lost card\"}").andExpect(status().isCreated());
    }

    @Test
    void customerCannotRaiseACaseOnSomeoneElsesAccount() throws Exception {
        postAs(BOB, "/api/cases", "{\"accountId\":1,\"subject\":\"Lost card\"}").andExpect(status().isNotFound());
    }

    @Test
    void supportCannotRaiseCases() throws Exception {
        postAs(SAM, "/api/cases", "{\"accountId\":1,\"subject\":\"Lost card\"}").andExpect(status().isForbidden());
    }
}
