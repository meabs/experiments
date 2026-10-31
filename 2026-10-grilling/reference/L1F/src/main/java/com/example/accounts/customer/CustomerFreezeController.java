package com.example.accounts.customer;

import java.util.List;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.account.Account;
import com.example.accounts.account.AccountController.AccountView;
import com.example.accounts.account.AccountNote;
import com.example.accounts.account.AccountNoteRepository;
import com.example.accounts.account.AccountFreezeController;
import com.example.accounts.account.AccountFreezeController.Reason;
import com.example.accounts.account.AccountRepository;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ForbiddenException;
import com.example.accounts.web.NotFoundException;

@RestController
public class CustomerFreezeController {

    private final CustomerRepository customers;
    private final AccountRepository accounts;
    private final AccountNoteRepository notes;
    private final CurrentUserProvider users;

    public CustomerFreezeController(CustomerRepository customers, AccountRepository accounts,
                                    AccountNoteRepository notes, CurrentUserProvider users) {
        this.customers = customers;
        this.accounts = accounts;
        this.notes = notes;
        this.users = users;
    }

    @PostMapping("/api/customers/{customerId}/freeze")
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    @Transactional
    public List<AccountView> freezeAll(@PathVariable String customerId, @RequestBody Reason body) {
        CurrentUser user = users.current();
        Customer customer = customers.findByIdAndTenantId(customerId, user.tenantId())
            .orElseThrow(() -> new NotFoundException("Customer not found"));
        if (!user.isAdmin()) {
            throw new ForbiddenException("Admins only");
        }
        String reason = AccountFreezeController.reason(body.reason());
        List<Account> held = accounts.findByTenantIdAndCustomerIdOrderById(customer.getTenantId(), customer.getId());
        for (Account a : held) {
            if (a.getStatus() == Account.Status.OPEN) {
                a.setStatus(Account.Status.FROZEN);
                accounts.save(a);
                notes.save(new AccountNote(a.getId(), user.id(), "Account frozen: " + reason, true));
            }
        }
        return held.stream().map(AccountView::of).toList();
    }
}
