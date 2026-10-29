package com.example.accounts.authz;

import static com.example.accounts.support.TestUsers.*;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;

import com.example.accounts.support.ApiTest;
import com.example.accounts.support.TestTokens;

/** Security tests for GET /api/customers/{customerId}/export. */
class S07AuthzTest extends ApiTest {

    @Test
    void customerExportsTheirDataWithoutRiskScore() throws Exception {
        getAs(ALICE, "/api/customers/c-1/export").andExpect(status().isOk())
            .andExpect(jsonPath("$.customer.id").value("c-1"))
            .andExpect(jsonPath("$.customer.riskScore").doesNotExist());
    }

    @Test
    void adminExportIncludesRiskScore() throws Exception {
        getAs(ADA, "/api/customers/c-1/export").andExpect(status().isOk()).andExpect(jsonPath("$.customer.riskScore").exists());
    }

    @Test
    void supportGets403() throws Exception {
        getAs(SAM, "/api/customers/c-1/export").andExpect(status().isForbidden());
    }

    @Test
    void anotherCustomerGets404() throws Exception {
        getAs(BOB, "/api/customers/c-1/export").andExpect(status().isNotFound());
    }
}
