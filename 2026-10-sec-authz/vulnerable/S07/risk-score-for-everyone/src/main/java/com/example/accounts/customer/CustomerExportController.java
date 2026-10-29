package com.example.accounts.customer;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.account.Account;
import com.example.accounts.account.AccountNote;
import com.example.accounts.account.AccountNoteRepository;
import com.example.accounts.account.AccountRepository;
import com.example.accounts.security.AccessPolicy;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ForbiddenException;
import com.example.accounts.web.NotFoundException;

@RestController
public class CustomerExportController {

    public record AccountItem(Long id, String nickname, String type, BigDecimal balance, String status) {
    }

    public record NoteItem(Long accountId, String body, boolean internal, Instant createdAt) {
    }

    private final CustomerRepository customers;
    private final AccountRepository accounts;
    private final AccountNoteRepository notes;
    private final AccessPolicy access;
    private final CurrentUserProvider users;

    public CustomerExportController(CustomerRepository customers, AccountRepository accounts, AccountNoteRepository notes,
                                    AccessPolicy access, CurrentUserProvider users) {
        this.customers = customers;
        this.accounts = accounts;
        this.notes = notes;
        this.access = access;
        this.users = users;
    }

    @GetMapping("/api/customers/{customerId}/export")
    @Transactional(readOnly = true)
    public Map<String, Object> export(@PathVariable String customerId) {
        CurrentUser user = users.current();
        Customer c = customers.findByIdAndTenantId(customerId, user.tenantId())
            .orElseThrow(() -> new NotFoundException("Customer not found"));
        boolean admin = access.isTenantAdmin(user, c.getTenantId());
        boolean self = access.isSelf(user, c);
        if (!admin && !self) {
            if (user.isSupport()) {
                throw new ForbiddenException("Support users cannot export customer data");
            }
            throw new NotFoundException("Customer not found");
        }
        Map<String, Object> customer = new LinkedHashMap<>();
        customer.put("id", c.getId());
        customer.put("name", c.getName());
        customer.put("email", c.getEmail());
        customer.put("phone", c.getPhone());
        customer.put("address", c.getAddress());
        customer.put("riskScore", c.getRiskScore());
        List<AccountItem> accountItems = new ArrayList<>();
        List<NoteItem> noteItems = new ArrayList<>();
        for (Account a : accounts.findByTenantIdAndCustomerIdOrderById(c.getTenantId(), c.getId())) {
            accountItems.add(new AccountItem(a.getId(), a.getNickname(), a.getType(), a.getBalance(), a.getStatus().name()));
            for (AccountNote n : notes.findByAccountIdOrderByCreatedAtDesc(a.getId())) {
                if (admin || !n.isInternal()) {
                    noteItems.add(new NoteItem(a.getId(), n.getBody(), n.isInternal(), n.getCreatedAt()));
                }
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("customer", customer);
        out.put("accounts", accountItems);
        out.put("notes", noteItems);
        return out;
    }
}
