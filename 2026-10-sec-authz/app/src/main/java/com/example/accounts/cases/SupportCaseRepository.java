package com.example.accounts.cases;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface SupportCaseRepository extends JpaRepository<SupportCase, String> {

    List<SupportCase> findByTenantIdOrderByOpenedAtDesc(String tenantId);

    List<SupportCase> findByTenantIdAndCustomerIdOrderByOpenedAtDesc(String tenantId, String customerId);

    List<SupportCase> findByTenantIdAndAssigneeUserIdOrderByOpenedAtDesc(String tenantId, String assigneeUserId);
}
