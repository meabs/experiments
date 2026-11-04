package com.example.accounts.account;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface SupportAssignmentRepository extends JpaRepository<SupportAssignment, Long> {

    boolean existsByTenantIdAndSupportUserIdAndAccountId(String tenantId, String supportUserId, Long accountId);

    List<SupportAssignment> findByTenantIdAndSupportUserId(String tenantId, String supportUserId);
}
