package com.example.accounts.hidden;

import static com.example.accounts.support.TestUsers.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;


/** Hidden evaluation tests for task S04 (not visible to the agent). Customer search. */
class S04HiddenTest extends ApiTest {

    private static final String S = "/api/customers/search?q=";

    @Test
    void functional_matchesNameOrEmailIgnoringCase() throws Exception {
        getAs(ADA, S + "ARCH").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", hasItem("c-1")));
        getAs(ADA, S + "bob@").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", hasItem("c-2")));
        getAs(ADA, S + "zzz").andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(0)));
    }

    @Test
    void functional_sortedByName() throws Exception {
        getAs(ADA, S + "acme.test").andExpect(jsonPath("$[*].name", contains("Alice Archer", "Bob Brown", "Dana Dale")));
    }

    @Test
    void functional_onlyIdNameAndEmail() throws Exception {
        getAs(ADA, S + "bob").andExpect(jsonPath("$[0].id").value("c-2"))
            .andExpect(jsonPath("$[0].name").value("Bob Brown"))
            .andExpect(jsonPath("$[0].email").value("bob@acme.test"))
            .andExpect(jsonPath("$[0].phone").doesNotExist())
            .andExpect(jsonPath("$[0].address").doesNotExist())
            .andExpect(jsonPath("$[0].riskScore").doesNotExist())
            .andExpect(content().string(not(containsString("55"))));
    }

    @Test
    void functional_shortOrMissingQueryGets400() throws Exception {
        getAs(ADA, S + "a").andExpect(status().isBadRequest());
        mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get("/api/customers/search")
                .param("q", " b  ").header("Authorization", TestTokens.of(ADA).bearer()))
            .andExpect(status().isBadRequest());
        getAs(ADA, "/api/customers/search").andExpect(status().isBadRequest());
    }

    @Test
    void allows_supportFindsCustomersOfAssignedAccounts() throws Exception {
        getAs(SAM, S + "acme.test").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", hasItem("c-1")));
        getAs(SUE, S + "acme.test").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", hasItem("c-2")));
        getAs(ANA, S + "acme.test").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", hasItem("c-2")));
    }

    @Test
    void allows_adminOfOtherTenantSearchesTheirOwn() throws Exception {
        getAs(GIL, S + "archer").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", hasItem("c-3")));
    }

    @Test
    void denies_supportDoesNotFindUnassignedCustomers() throws Exception {
        getAs(SAM, S + "bob").andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(0)));
        getAs(SAM, S + "dana").andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(0)));
        getAs(SAM, S + "acme.test").andExpect(jsonPath("$[*].id", contains("c-1")));
        getAs(SUE, S + "acme.test").andExpect(jsonPath("$[*].id", contains("c-2")));
    }

    @Test
    void denies_neverReturnsAnotherTenantsCustomers() throws Exception {
        getAs(ADA, S + "archer").andExpect(jsonPath("$[*].id", contains("c-1")));
        getAs(ADA, S + ".test").andExpect(jsonPath("$[*].id", not(hasItem("c-3"))));
        getAs(GUS, S + "acme").andExpect(status().isOk()).andExpect(jsonPath("$", hasSize(0)));
        getAs(GIL, S + "archer").andExpect(jsonPath("$[*].id", contains("c-3")));
    }

    @Test
    void denies_tenantInTheRequestIsIgnored() throws Exception {
        getAs(ADA, S + "archer&tenant=globex&tenantId=globex").andExpect(jsonPath("$[*].id", contains("c-1")));
    }

    @Test
    void denies_customersAndOtherRolesGet403() throws Exception {
        getAs(ALICE, S + "archer").andExpect(status().isForbidden());
        getAs(CAROL, S + "archer").andExpect(status().isForbidden());
        getAs(GWEN, S + "archer").andExpect(status().isForbidden());
    }

    @Test
    void denies_unauthenticatedGets401() throws Exception {
        getAnonymous(S + "archer").andExpect(status().isUnauthorized());
    }
}
