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


/** Hidden evaluation tests for task S05 (not visible to the agent). Staff view of a support case. */
class S05HiddenTest extends ApiTest {

    private static final String K = "/api/support/cases/";

    @Test
    void functional_caseWithCommentsOldestFirst() throws Exception {
        getAs(SAM, K + "k-1").andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value("k-1"))
            .andExpect(jsonPath("$.accountId").value(1))
            .andExpect(jsonPath("$.customerId").value("c-1"))
            .andExpect(jsonPath("$.subject").value("Card not arrived"))
            .andExpect(jsonPath("$.status").value("OPEN"))
            .andExpect(jsonPath("$.assigneeUserId").value("u-sam"))
            .andExpect(jsonPath("$.comments[*].author", contains("u-alice", "u-sam")))
            .andExpect(jsonPath("$.comments[0].internal").value(false))
            .andExpect(jsonPath("$.comments[0].createdAt").exists());
    }

    @Test
    void functional_includesInternalComments() throws Exception {
        getAs(SUE, K + "k-2").andExpect(status().isOk())
            .andExpect(jsonPath("$.comments[0].internal").value(true))
            .andExpect(jsonPath("$.comments[0].body", containsString("chargebacks")));
    }

    @Test
    void allows_assigneeSeesTheirCases() throws Exception {
        getAs(SUE, K + "k-3").andExpect(status().isOk());
        getAs(GUS, K + "k-4").andExpect(status().isOk());
    }

    @Test
    void allows_adminSeesAnyCaseInTenantIncludingUnassigned() throws Exception {
        getAs(ADA, K + "k-2").andExpect(status().isOk());
        getAs(ADA, K + "k-5").andExpect(status().isOk()).andExpect(jsonPath("$.assigneeUserId").value(nullValue()));
        getAs(AL, K + "k-1").andExpect(status().isOk());
    }

    @Test
    void denies_supportAssignedToTheAccountButNotTheCase() throws Exception {
        getAs(SAM, K + "k-2").andExpect(status().isNotFound()).andExpect(content().string(not(containsString("chargebacks"))));
        getAs(ANA, K + "k-3").andExpect(status().isNotFound());
    }

    @Test
    void denies_supportCannotSeeUnassignedCases() throws Exception {
        getAs(SUE, K + "k-5").andExpect(status().isNotFound());
        getAs(ANA, K + "k-5").andExpect(status().isNotFound());
        getAs(SAM, K + "k-3").andExpect(status().isNotFound());
    }

    @Test
    void denies_customersGet403EvenForTheirOwnCase() throws Exception {
        getAs(ALICE, K + "k-1").andExpect(status().isForbidden());
        getAs(ALICE, K + "k-2").andExpect(status().isForbidden()).andExpect(content().string(not(containsString("chargebacks"))));
    }

    @Test
    void denies_otherRolesGet403() throws Exception {
        getAs(GWEN, K + "k-4").andExpect(status().isForbidden());
    }

    @Test
    void denies_otherTenantGets404() throws Exception {
        getAs(GIL, K + "k-1").andExpect(status().isNotFound());
        getAs(GUS, K + "k-1").andExpect(status().isNotFound());
        getAs(ADA, K + "k-4").andExpect(status().isNotFound());
    }

    @Test
    void denies_missingCaseGets404() throws Exception {
        getAs(ADA, K + "k-999").andExpect(status().isNotFound());
    }

    @Test
    void denies_unauthenticatedGets401() throws Exception {
        getAnonymous(K + "k-1").andExpect(status().isUnauthorized());
    }
}
