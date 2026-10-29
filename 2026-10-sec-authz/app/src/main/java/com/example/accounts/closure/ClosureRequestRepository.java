package com.example.accounts.closure;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface ClosureRequestRepository extends JpaRepository<ClosureRequest, Long> {

    List<ClosureRequest> findByTenantIdAndStatusOrderByRequestedAt(String tenantId, String status);

    boolean existsByAccountIdAndStatus(Long accountId, String status);
}
