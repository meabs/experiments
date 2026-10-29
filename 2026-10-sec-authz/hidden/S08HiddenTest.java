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

/** Hidden evaluation tests for task S08 (not visible to the agent). Changing account settings. */
class S08HiddenTest extends ApiTest {

    private static final String A1 = "/api/accounts/1";

    @Autowired
    AccountRepository accounts;

    private void same(long id, String nickname, int limit) {
        Account a = accounts.findById(id).orElseThrow();
        assertThat(a.getNickname()).isEqualTo(nickname);
        assertThat(a.getDailyLimit()).isEqualTo(limit);
    }

    @Test
    void functional_holderRenamesTrimmedAndLimitStays() throws Exception {
        patchAs(ALICE, A1, "{\"nickname\":\"  Bills  \"}").andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(1)).andExpect(jsonPath("$.nickname").value("Bills"))
            .andExpect(jsonPath("$.dailyLimit").value(500));
        same(1, "Bills", 500);
    }

    @Test
    void functional_adminChangesTheLimit() throws Exception {
        patchAs(ADA, "/api/accounts/3", "{\"dailyLimit\":1000}").andExpect(status().isOk())
            .andExpect(jsonPath("$.dailyLimit").value(1000));
        same(3, "Main", 1000);
        patchAs(ADA, A1, "{\"dailyLimit\":0}").andExpect(status().isOk());
        same(1, "Everyday", 0);
    }

    @Test
    void functional_invalidValuesGet400AndChangeNothing() throws Exception {
        patchAs(ALICE, A1, "{\"nickname\":\"   \"}").andExpect(status().isBadRequest());
        patchAs(ALICE, A1, "{\"nickname\":\"" + "x".repeat(41) + "\"}").andExpect(status().isBadRequest());
        patchAs(ADA, A1, "{\"dailyLimit\":5001}").andExpect(status().isBadRequest());
        patchAs(ADA, A1, "{\"dailyLimit\":-1}").andExpect(status().isBadRequest());
        patchAs(ADA, A1, "{\"dailyLimit\":12.5}").andExpect(status().isBadRequest());
        patchAs(ADA, A1, "{}").andExpect(status().isBadRequest());
        same(1, "Everyday", 500);
    }

    @Test
    void functional_closedAccountGets409() throws Exception {
        patchAs(ADA, "/api/accounts/5", "{\"dailyLimit\":100}").andExpect(status().isConflict());
        patchAs(DANA, "/api/accounts/5", "{\"nickname\":\"Reopened\"}").andExpect(status().isConflict());
        same(5, "Old ISA", 0);
    }

    @Test
    void allows_adminApproverChangesLimit() throws Exception {
        patchAs(AL, "/api/accounts/2", "{\"dailyLimit\":300}").andExpect(status().isOk());
        same(2, "Rainy day", 300);
        patchAs(GIL, "/api/accounts/4", "{\"dailyLimit\":900}").andExpect(status().isOk());
    }

    @Test
    void denies_holderCannotChangeTheLimit() throws Exception {
        patchAs(ALICE, A1, "{\"dailyLimit\":5000}").andExpect(status().isForbidden());
        same(1, "Everyday", 500);
    }

    @Test
    void denies_holderRequestWithLimitIsRefusedAsAWhole() throws Exception {
        patchAs(ALICE, A1, "{\"nickname\":\"Sneaky\",\"dailyLimit\":100}").andExpect(status().isForbidden());
        patchAs(ALICE, A1, "{\"nickname\":\"Sneaky\",\"dailyLimit\":500}").andExpect(status().isForbidden());
        same(1, "Everyday", 500);
    }

    @Test
    void denies_assignedSupportChangesNothing() throws Exception {
        patchAs(SAM, A1, "{\"nickname\":\"Support was here\"}").andExpect(status().isForbidden());
        patchAs(ANA, "/api/accounts/3", "{\"dailyLimit\":10}").andExpect(status().isForbidden());
        same(1, "Everyday", 500);
        same(3, "Main", 500);
    }

    @Test
    void denies_othersGet404() throws Exception {
        patchAs(BOB, A1, "{\"nickname\":\"Mine now\"}").andExpect(status().isNotFound());
        patchAs(SUE, A1, "{\"nickname\":\"Mine now\"}").andExpect(status().isNotFound());
        patchAs(GIL, A1, "{\"dailyLimit\":5000}").andExpect(status().isNotFound());
        patchAs(CAROL, A1, "{\"nickname\":\"Mine now\"}").andExpect(status().isNotFound());
        patchAs(ADA, "/api/accounts/4", "{\"dailyLimit\":5000}").andExpect(status().isNotFound());
        same(1, "Everyday", 500);
        same(4, "Joint", 700);
    }

    @Test
    void denies_withoutWriteScopeGets403() throws Exception {
        patchWith(TestTokens.of(ALICE).scopes("accounts:read"), A1, "{\"nickname\":\"Bills\"}").andExpect(status().isForbidden());
        patchWith(TestTokens.of(ADA).scopes("accounts:read"), A1, "{\"dailyLimit\":1}").andExpect(status().isForbidden());
        patchWith(TestTokens.of(BOB).scopes("accounts:read"), A1, "{\"nickname\":\"Bills\"}").andExpect(status().isForbidden());
        same(1, "Everyday", 500);
    }

    @Test
    void denies_missingAccountGets404() throws Exception {
        patchAs(ADA, "/api/accounts/999", "{\"dailyLimit\":1}").andExpect(status().isNotFound());
    }

    @Test
    void denies_unauthenticatedGets401() throws Exception {
        mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch(A1)
                .contentType(org.springframework.http.MediaType.APPLICATION_JSON).content("{\"nickname\":\"x\"}"))
            .andExpect(status().isUnauthorized());
        same(1, "Everyday", 500);
    }
}
