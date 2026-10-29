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

import com.example.accounts.account.Account;
import com.example.accounts.account.AccountRepository;
import com.example.accounts.closure.ClosureRequest;
import com.example.accounts.closure.ClosureRequestRepository;

/** Hidden evaluation tests for task S03 (not visible to the agent). Approving and rejecting closure requests. */
class S03HiddenTest extends ApiTest {

    @Autowired
    ClosureRequestRepository requests;

    @Autowired
    AccountRepository accounts;

    private void pending(long requestId, long accountId) {
        ClosureRequest r = requests.findById(requestId).orElseThrow();
        assertThat(r.getStatus()).isEqualTo(ClosureRequest.Status.PENDING);
        assertThat(r.getDecidedBy()).isNull();
        assertThat(accounts.findById(accountId).orElseThrow().getStatus()).isEqualTo(Account.Status.OPEN);
    }

    @Test
    void functional_approveRecordsDecisionAndClosesAccount() throws Exception {
        postAs(ANA, "/api/closure-requests/1/approve", null).andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(1))
            .andExpect(jsonPath("$.status").value("APPROVED"))
            .andExpect(jsonPath("$.decidedBy").value("u-ana"));
        ClosureRequest r = requests.findById(1L).orElseThrow();
        assertThat(r.getStatus()).isEqualTo(ClosureRequest.Status.APPROVED);
        assertThat(r.getDecidedBy()).isEqualTo("u-ana");
        assertThat(r.getDecidedAt()).isNotNull();
        assertThat(accounts.findById(2L).orElseThrow().getStatus()).isEqualTo(Account.Status.CLOSED);
    }

    @Test
    void functional_rejectRecordsDecisionAndKeepsAccountOpen() throws Exception {
        postAs(ANA, "/api/closure-requests/1/reject", null).andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("REJECTED")).andExpect(jsonPath("$.decidedBy").value("u-ana"));
        ClosureRequest r = requests.findById(1L).orElseThrow();
        assertThat(r.getStatus()).isEqualTo(ClosureRequest.Status.REJECTED);
        assertThat(r.getDecidedAt()).isNotNull();
        assertThat(accounts.findById(2L).orElseThrow().getStatus()).isEqualTo(Account.Status.OPEN);
    }

    @Test
    void functional_decidedRequestGets409() throws Exception {
        postAs(ANA, "/api/closure-requests/3/approve", null).andExpect(status().isConflict());
        postAs(ANA, "/api/closure-requests/3/reject", null).andExpect(status().isConflict());
        postAs(ANA, "/api/closure-requests/1/approve", null).andExpect(status().isOk());
        postAs(AL, "/api/closure-requests/1/reject", null).andExpect(status().isConflict());
        assertThat(requests.findById(1L).orElseThrow().getStatus()).isEqualTo(ClosureRequest.Status.APPROVED);
    }

    @Test
    void allows_anyApproverOfTheTenant() throws Exception {
        postAs(AL, "/api/closure-requests/1/approve", null).andExpect(status().isOk());
        postAs(GWEN, "/api/closure-requests/4/approve", null).andExpect(status().isOk());
        assertThat(accounts.findById(4L).orElseThrow().getStatus()).isEqualTo(Account.Status.CLOSED);
    }

    @Test
    void denies_selfApprovalAndSelfRejection() throws Exception {
        postAs(AL, "/api/closure-requests/2/approve", null).andExpect(status().isForbidden());
        postAs(AL, "/api/closure-requests/2/reject", null).andExpect(status().isForbidden());
        pending(2, 3);
    }

    @Test
    void denies_adminWithoutApproverRole() throws Exception {
        postAs(ADA, "/api/closure-requests/1/approve", null).andExpect(status().isForbidden());
        postAs(ADA, "/api/closure-requests/1/reject", null).andExpect(status().isForbidden());
        pending(1, 2);
    }

    @Test
    void denies_supportAndCustomers() throws Exception {
        postAs(SAM, "/api/closure-requests/1/approve", null).andExpect(status().isForbidden());
        postAs(ALICE, "/api/closure-requests/1/approve", null).andExpect(status().isForbidden());
        postAs(BOB, "/api/closure-requests/1/reject", null).andExpect(status().isForbidden());
        pending(1, 2);
    }

    @Test
    void denies_roleIsCheckedBeforeTheRequest() throws Exception {
        postAs(ADA, "/api/closure-requests/999/approve", null).andExpect(status().isForbidden());
        postAs(ADA, "/api/closure-requests/4/approve", null).andExpect(status().isForbidden());
    }

    @Test
    void denies_otherTenantsRequestGets404() throws Exception {
        postAs(GWEN, "/api/closure-requests/1/approve", null).andExpect(status().isNotFound());
        postAs(ANA, "/api/closure-requests/4/approve", null).andExpect(status().isNotFound());
        postAs(ANA, "/api/closure-requests/4/reject", null).andExpect(status().isNotFound());
        pending(1, 2);
        pending(4, 4);
    }

    @Test
    void denies_unknownRequestGets404() throws Exception {
        postAs(ANA, "/api/closure-requests/999/approve", null).andExpect(status().isNotFound());
    }

    @Test
    void denies_unauthenticatedGets401() throws Exception {
        mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post("/api/closure-requests/1/approve"))
            .andExpect(status().isUnauthorized());
        pending(1, 2);
    }
}
