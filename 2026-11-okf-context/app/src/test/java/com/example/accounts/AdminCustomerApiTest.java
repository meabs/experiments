package com.example.accounts;

import static com.example.accounts.support.TestUsers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;

class AdminCustomerApiTest extends ApiTest {

    @Test
    void adminSeesCustomerInTheirTenant() throws Exception {
        getAs(ADA, "/api/admin/customers/c-2").andExpect(status().isOk()).andExpect(jsonPath("$.riskScore").value(55));
    }

    @Test
    void customerInAnotherTenantIsNotFound() throws Exception {
        getAs(ADA, "/api/admin/customers/c-3").andExpect(status().isNotFound());
    }

    @Test
    void nonAdminsAreForbidden() throws Exception {
        getAs(ALICE, "/api/admin/customers/c-1").andExpect(status().isForbidden());
        getAs(SAM, "/api/admin/customers/c-1").andExpect(status().isForbidden());
    }

    @Test
    void meShowsTheCaller() throws Exception {
        getAs(ANA, "/api/me").andExpect(jsonPath("$.id").value("u-ana")).andExpect(jsonPath("$.tenantId").value("acme"));
    }
}
