package com.example.accounts;

import static com.example.accounts.support.TestUsers.*;
import static org.hamcrest.Matchers.containsInAnyOrder;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;

class ClosureApiTest extends ApiTest {

    @Test
    void ownerAsksToCloseTheirAccount() throws Exception {
        postAs(ALICE, "/api/accounts/1/closure-requests", null).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("PENDING")).andExpect(jsonPath("$.requestedBy").value("u-alice"));
    }

    @Test
    void secondPendingRequestConflicts() throws Exception {
        postAs(ALICE, "/api/accounts/2/closure-requests", null).andExpect(status().isConflict());
    }

    @Test
    void assignedSupportCannotAskToClose() throws Exception {
        postAs(SAM, "/api/accounts/1/closure-requests", null).andExpect(status().isForbidden());
    }

    @Test
    void approverSeesPendingRequestsInTheirTenant() throws Exception {
        getAs(ANA, "/api/closure-requests").andExpect(status().isOk()).andExpect(jsonPath("$[*].id", containsInAnyOrder(1, 2)));
        getAs(GWEN, "/api/closure-requests").andExpect(jsonPath("$[*].id", containsInAnyOrder(4)));
    }

    @Test
    void onlyApproversSeePendingRequests() throws Exception {
        getAs(ADA, "/api/closure-requests").andExpect(status().isForbidden());
        getAs(ALICE, "/api/closure-requests").andExpect(status().isForbidden());
    }
}
