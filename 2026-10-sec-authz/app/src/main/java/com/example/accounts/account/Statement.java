package com.example.accounts.account;

import java.math.BigDecimal;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** A monthly statement, e.g. period "2026-09". */
@Entity
@Table(name = "statements")
public class Statement {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Long accountId;

    @Column(nullable = false)
    private String period;

    @Column(nullable = false)
    private BigDecimal openingBalance;

    @Column(nullable = false)
    private BigDecimal closingBalance;

    public Long getId() { return id; }
    public Long getAccountId() { return accountId; }
    public String getPeriod() { return period; }
    public BigDecimal getOpeningBalance() { return openingBalance; }
    public BigDecimal getClosingBalance() { return closingBalance; }
}
