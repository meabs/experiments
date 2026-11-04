package com.example.accounts.customer;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.NotFoundException;

/** Back-office view of a customer, for admins of the customer's tenant. */
@RestController
@RequestMapping("/api/admin/customers")
public class AdminCustomerController {

    public record AdminCustomerView(String id, String name, String email, String phone, String address, int riskScore) {
        static AdminCustomerView of(Customer c) {
            return new AdminCustomerView(c.getId(), c.getName(), c.getEmail(), c.getPhone(), c.getAddress(), c.getRiskScore());
        }
    }

    private final CustomerRepository customers;
    private final CurrentUserProvider users;

    public AdminCustomerController(CustomerRepository customers, CurrentUserProvider users) {
        this.customers = customers;
        this.users = users;
    }

    @GetMapping("/{customerId}")
    @PreAuthorize("hasRole('ADMIN')")
    public AdminCustomerView get(@PathVariable String customerId) {
        CurrentUser user = users.current();
        // Only within the admin's own tenant; a customer of another tenant is "not found".
        Customer c = customers.findByIdAndTenantId(customerId, user.tenantId())
            .orElseThrow(() -> new NotFoundException("Customer not found"));
        return AdminCustomerView.of(c);
    }
}
