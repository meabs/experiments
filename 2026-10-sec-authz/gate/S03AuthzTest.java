package com.example.accounts.authz;

import static com.example.accounts.support.TestUsers.*;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

/** Security tests for POST /api/closure-requests/{requestId}/approve and /reject. */
class S03AuthzTest extends ApiTest {

    @Test
    void approverApproves() throws Exception {
        postAs(ANA, "/api/closure-requests/1/approve", null).andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("APPROVED"));
    }

    @Test
    void approverRejects() throws Exception {
        postAs(ANA, "/api/closure-requests/1/reject", null).andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("REJECTED"));
    }

    @Test
    void customerCannotApprove() throws Exception {
        postAs(ALICE, "/api/closure-requests/1/approve", null).andExpect(status().isForbidden());
    }

    @Test
    void unauthenticatedIsRejected() throws Exception {
        mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post("/api/closure-requests/1/approve"))
            .andExpect(status().isUnauthorized());
    }
}
