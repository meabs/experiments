package com.example.accounts.security;

import org.springframework.stereotype.Component;

import com.example.accounts.account.Account;
import com.example.accounts.account.SupportAssignmentRepository;
import com.example.accounts.customer.Customer;
import com.example.accounts.customer.CustomerRepository;

/**
 * Resource-level access rules shared by the services. Never cross tenants: every rule first checks that the resource is
 * in the caller's tenant.
 */
@Component
public class AccessPolicy {

    private final CustomerRepository customers;
    private final SupportAssignmentRepository assignments;

    public AccessPolicy(CustomerRepository customers, SupportAssignmentRepository assignments) {
        this.customers = customers;
        this.assignments = assignments;
    }

    /** The caller is the customer who owns this customer record. */
    public boolean isSelf(CurrentUser user, Customer customer) {
        return user.isCustomer() && user.inTenant(customer.getTenantId()) && user.id().equals(customer.getUserId());
    }

    /** The caller is the customer who owns the account. */
    public boolean ownsAccount(CurrentUser user, Account account) {
        if (!user.isCustomer() || !user.inTenant(account.getTenantId())) {
            return false;
        }
        return customers.findById(account.getCustomerId()).map(c -> user.id().equals(c.getUserId())).orElse(false);
    }

    /** The caller is a support user assigned to the account. */
    public boolean isAssignedSupport(CurrentUser user, Account account) {
        return user.isSupport() && user.inTenant(account.getTenantId())
            && assignments.existsByTenantIdAndSupportUserIdAndAccountId(account.getTenantId(), user.id(), account.getId());
    }

    /** Who may see an account: its owner, support users assigned to it, and admins of its tenant. */
    public boolean canViewAccount(CurrentUser user, Account account) {
        if (!user.inTenant(account.getTenantId())) {
            return false;
        }
        return user.isAdmin() || isAssignedSupport(user, account) || ownsAccount(user, account);
    }

    /** Admin of the resource's tenant. */
    public boolean isTenantAdmin(CurrentUser user, String tenantId) {
        return user.isAdmin() && user.inTenant(tenantId);
    }
}
