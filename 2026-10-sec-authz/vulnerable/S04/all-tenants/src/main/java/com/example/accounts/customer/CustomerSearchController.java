package com.example.accounts.customer;

import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.account.AccountRepository;
import com.example.accounts.account.SupportAssignment;
import com.example.accounts.account.SupportAssignmentRepository;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;

@RestController
public class CustomerSearchController {

    public record CustomerHit(String id, String name, String email) {
    }

    private final CustomerRepository customers;
    private final AccountRepository accounts;
    private final SupportAssignmentRepository assignments;
    private final CurrentUserProvider users;

    public CustomerSearchController(CustomerRepository customers, AccountRepository accounts,
                                    SupportAssignmentRepository assignments, CurrentUserProvider users) {
        this.customers = customers;
        this.accounts = accounts;
        this.assignments = assignments;
        this.users = users;
    }

    @GetMapping("/api/customers/search")
    @PreAuthorize("hasAnyRole('SUPPORT', 'ADMIN')")
    @Transactional(readOnly = true)
    public List<CustomerHit> search(@RequestParam(required = false) String q) {
        String term = q == null ? "" : q.trim().toLowerCase(Locale.ROOT);
        if (term.length() < 2) {
            throw new IllegalArgumentException("q must have at least 2 characters");
        }
        CurrentUser user = users.current();
        Set<String> allowed = null; // null: every customer in the tenant
        if (!user.isAdmin()) {
            List<Long> ids = assignments.findByTenantIdAndSupportUserId(user.tenantId(), user.id()).stream()
                .map(SupportAssignment::getAccountId).toList();
            allowed = new HashSet<>();
            for (var a : accounts.findAllById(ids)) {
                if (user.inTenant(a.getTenantId())) {
                    allowed.add(a.getCustomerId());
                }
            }
        }
        Set<String> only = allowed;
        return customers.findAll(org.springframework.data.domain.Sort.by("name")).stream()
            .filter(c -> only == null || only.contains(c.getId()))
            .filter(c -> c.getName().toLowerCase(Locale.ROOT).contains(term)
                || (c.getEmail() != null && c.getEmail().toLowerCase(Locale.ROOT).contains(term)))
            .map(c -> new CustomerHit(c.getId(), c.getName(), c.getEmail()))
            .toList();
    }
}
