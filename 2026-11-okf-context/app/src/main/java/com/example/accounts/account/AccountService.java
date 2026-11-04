package com.example.accounts.account;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.accounts.customer.CustomerRepository;
import com.example.accounts.security.AccessPolicy;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.NotFoundException;

@Service
@Transactional(readOnly = true)
public class AccountService {

    private final AccountRepository accounts;
    private final CustomerRepository customers;
    private final SupportAssignmentRepository assignments;
    private final TransactionRepository transactions;
    private final AccessPolicy access;
    private final CurrentUserProvider users;

    public AccountService(AccountRepository accounts, CustomerRepository customers, SupportAssignmentRepository assignments,
                          TransactionRepository transactions, AccessPolicy access, CurrentUserProvider users) {
        this.accounts = accounts;
        this.customers = customers;
        this.assignments = assignments;
        this.transactions = transactions;
        this.access = access;
        this.users = users;
    }

    /**
     * The account, if the caller may see it. An account the caller may not see answers 404 exactly like one that does
     * not exist, so the API does not reveal which account ids exist.
     */
    public Account getVisible(Long accountId) {
        CurrentUser user = users.current();
        return accounts.findById(accountId)
            .filter(a -> access.canViewAccount(user, a))
            .orElseThrow(() -> new NotFoundException("Account not found"));
    }

    /** Accounts the caller may see: their own (customers), assigned ones (support), all in the tenant (admins). */
    public List<Account> listVisible() {
        CurrentUser user = users.current();
        if (user.isAdmin()) {
            return accounts.findByTenantIdOrderById(user.tenantId());
        }
        if (user.isSupport()) {
            List<Long> ids = assignments.findByTenantIdAndSupportUserId(user.tenantId(), user.id()).stream()
                .map(SupportAssignment::getAccountId).toList();
            return accounts.findAllById(ids).stream().filter(a -> user.inTenant(a.getTenantId())).toList();
        }
        if (user.isCustomer()) {
            return customers.findByUserId(user.id())
                .filter(c -> user.inTenant(c.getTenantId()))
                .map(c -> accounts.findByTenantIdAndCustomerIdOrderById(user.tenantId(), c.getId()))
                .orElse(List.of());
        }
        return List.of();
    }

    public List<Transaction> transactions(Long accountId) {
        return transactions.findByAccountIdOrderByBookedOnDescIdDesc(getVisible(accountId).getId());
    }
}
