package com.example.accounts.security;

import java.util.Set;

/** The caller, as stated by their token. Roles are without the ROLE_ prefix, scopes without SCOPE_. */
public record CurrentUser(String id, String tenantId, Set<String> roles, Set<String> scopes) {

    public static final String CUSTOMER = "CUSTOMER";
    public static final String SUPPORT = "SUPPORT";
    public static final String ADMIN = "ADMIN";
    public static final String APPROVER = "APPROVER";

    public boolean hasRole(String role) {
        return roles.contains(role);
    }

    public boolean hasScope(String scope) {
        return scopes.contains(scope);
    }

    public boolean isCustomer() {
        return hasRole(CUSTOMER);
    }

    public boolean isSupport() {
        return hasRole(SUPPORT);
    }

    public boolean isAdmin() {
        return hasRole(ADMIN);
    }

    public boolean inTenant(String tenant) {
        return tenantId != null && tenantId.equals(tenant);
    }
}
