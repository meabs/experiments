package com.example.accounts.customer;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.security.AccessPolicy;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ForbiddenException;
import com.example.accounts.web.NotFoundException;

@RestController
public class CustomerContactController {

    public record ContactChange(@NotBlank @Email String email, @NotBlank @Pattern(regexp = "\\+?[0-9 ]{7,20}") String phone) {
    }

    public record ContactView(String id, String email, String phone) {
    }

    private final CustomerRepository customers;
    private final AccessPolicy access;
    private final CurrentUserProvider users;

    public CustomerContactController(CustomerRepository customers, AccessPolicy access, CurrentUserProvider users) {
        this.customers = customers;
        this.access = access;
        this.users = users;
    }

    @PutMapping("/api/customers/{customerId}/contact")
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    @Transactional
    public ContactView update(@PathVariable String customerId, @Valid @RequestBody ContactChange change) {
        CurrentUser user = users.current();
        Customer c = customers.findById(customerId)
            .orElseThrow(() -> new NotFoundException("Customer not found"));
        boolean self = access.isSelf(user, c);
        if (user.isCustomer() && !self && !user.isAdmin()) {
            throw new NotFoundException("Customer not found");
        }
        if (!self && !user.isAdmin()) {
            throw new ForbiddenException("Only the customer or an admin can change contact details");
        }
        c.setEmail(change.email().trim());
        c.setPhone(change.phone().trim());
        return new ContactView(c.getId(), c.getEmail(), c.getPhone());
    }
}
