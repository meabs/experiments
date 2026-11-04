package com.example.accounts.payment;

import java.time.Instant;
import java.time.LocalDate;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface PaymentRepository extends JpaRepository<Payment, Long> {

    List<Payment> findByAccountIdAndCreatedAtGreaterThanEqual(Long accountId, Instant from);

    List<Payment> findByStatusAndExecutionDateLessThanEqualOrderById(String status, LocalDate date);
}
