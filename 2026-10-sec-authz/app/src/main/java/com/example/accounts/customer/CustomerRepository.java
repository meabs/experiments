package com.example.accounts.customer;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface CustomerRepository extends JpaRepository<Customer, String> {

    Optional<Customer> findByUserId(String userId);

    Optional<Customer> findByIdAndTenantId(String id, String tenantId);

    List<Customer> findByTenantIdOrderByName(String tenantId);
}
