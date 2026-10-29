package com.example.accounts.account;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface AccountRepository extends JpaRepository<Account, Long> {

    List<Account> findByTenantIdOrderById(String tenantId);

    List<Account> findByTenantIdAndCustomerIdOrderById(String tenantId, String customerId);
}
