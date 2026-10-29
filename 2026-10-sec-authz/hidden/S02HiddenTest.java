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

import com.example.accounts.customer.Customer;
import com.example.accounts.customer.CustomerRepository;

/** Hidden evaluation tests for task S02 (not visible to the agent). Contact details. */
class S02HiddenTest extends ApiTest {

    private static final String C1 = "/api/customers/c-1/contact";
    private static final String GOOD = "{\"email\":\"alice.new@acme.test\",\"phone\":\"+44 7700 900123\"}";

    @Autowired
    CustomerRepository customers;

    private void unchanged(String id, String email, String phone) {
        Customer c = customers.findById(id).orElseThrow();
        assertThat(c.getEmail()).isEqualTo(email);
        assertThat(c.getPhone()).isEqualTo(phone);
    }

    private void aliceUnchanged() {
        unchanged("c-1", "alice@acme.test", "01632 960101");
    }

    @Test
    void functional_savesBothAndKeepsOtherFields() throws Exception {
        putAs(ALICE, C1, GOOD).andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value("c-1"))
            .andExpect(jsonPath("$.email").value("alice.new@acme.test"))
            .andExpect(jsonPath("$.phone").value("+44 7700 900123"));
        Customer c = customers.findById("c-1").orElseThrow();
        assertThat(c.getEmail()).isEqualTo("alice.new@acme.test");
        assertThat(c.getPhone()).isEqualTo("+44 7700 900123");
        assertThat(c.getAddress()).isEqualTo("1 Mill Lane, York");
        assertThat(c.getName()).isEqualTo("Alice Archer");
        assertThat(c.getRiskScore()).isEqualTo(12);
    }

    @Test
    void functional_invalidInputGets400AndChangesNothing() throws Exception {
        putAs(ALICE, C1, "{\"email\":\"not-an-email\",\"phone\":\"01632 960999\"}").andExpect(status().isBadRequest());
        putAs(ALICE, C1, "{\"email\":\"a@acme.test\",\"phone\":\"call me\"}").andExpect(status().isBadRequest());
        putAs(ALICE, C1, "{\"email\":\"a@acme.test\",\"phone\":\"12345\"}").andExpect(status().isBadRequest());
        putAs(ALICE, C1, "{\"email\":\"a@acme.test\"}").andExpect(status().isBadRequest());
        aliceUnchanged();
    }

    @Test
    void allows_tenantAdminUpdatesAnyCustomerInTenant() throws Exception {
        putAs(ADA, "/api/customers/c-2/contact", "{\"email\":\"bob2@acme.test\",\"phone\":\"01632 960999\"}")
            .andExpect(status().isOk());
        unchanged("c-2", "bob2@acme.test", "01632 960999");
        putAs(AL, C1, GOOD).andExpect(status().isOk());
    }

    @Test
    void denies_otherCustomerGets404() throws Exception {
        putAs(BOB, C1, GOOD).andExpect(status().isNotFound());
        aliceUnchanged();
    }

    @Test
    void denies_supportGets403EvenWhenAssigned() throws Exception {
        putAs(SAM, C1, GOOD).andExpect(status().isForbidden());
        putAs(ANA, "/api/customers/c-2/contact", GOOD).andExpect(status().isForbidden());
        aliceUnchanged();
        unchanged("c-2", "bob@acme.test", "01632 960102");
    }

    @Test
    void denies_otherTenantGets404() throws Exception {
        putAs(GIL, C1, GOOD).andExpect(status().isNotFound());
        putAs(CAROL, C1, GOOD).andExpect(status().isNotFound());
        putAs(ADA, "/api/customers/c-3/contact", GOOD).andExpect(status().isNotFound());
        aliceUnchanged();
        unchanged("c-3", "carol@globex.test", "01632 960203");
    }

    @Test
    void denies_withoutWriteScopeGets403() throws Exception {
        putWith(TestTokens.of(ALICE).scopes("accounts:read"), C1, GOOD).andExpect(status().isForbidden());
        putWith(TestTokens.of(ADA).scopes("accounts:read"), C1, GOOD).andExpect(status().isForbidden());
        putWith(TestTokens.of(ALICE).scopes("accounts:writer accounts:read"), C1, GOOD).andExpect(status().isForbidden());
        aliceUnchanged();
    }

    @Test
    void denies_scopeIsCheckedBeforeTheCustomer() throws Exception {
        putWith(TestTokens.of(BOB).scopes("accounts:read"), C1, GOOD).andExpect(status().isForbidden());
    }

    @Test
    void denies_unknownCustomerGets404() throws Exception {
        putAs(ADA, "/api/customers/c-999/contact", GOOD).andExpect(status().isNotFound());
    }

    @Test
    void denies_unauthenticatedGets401() throws Exception {
        mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put(C1)
                .contentType(org.springframework.http.MediaType.APPLICATION_JSON).content(GOOD))
            .andExpect(status().isUnauthorized());
        aliceUnchanged();
    }
}
