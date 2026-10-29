package com.example.accounts.account;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface StatementRepository extends JpaRepository<Statement, Long> {

    List<Statement> findByAccountIdOrderByPeriodDesc(Long accountId);
}
