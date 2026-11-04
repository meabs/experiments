package com.example.accounts.account;

import java.math.BigDecimal;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "accounts")
public class Account {

    public enum Status { OPEN, CLOSED }

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String tenantId;

    @Column(nullable = false)
    private String customerId;

    @Column(nullable = false)
    private String sortCode;

    @Column(nullable = false)
    private String accountNumber;

    private String nickname;

    @Column(nullable = false)
    private String type;

    @Column(nullable = false)
    private BigDecimal balance;

    /** Most the customer can pay out in a day, in pounds. Set by the bank (admins), not by the customer. */
    @Column(nullable = false)
    private int dailyLimit;

    @Column(nullable = false)
    private String status;

    public Long getId() { return id; }
    public String getTenantId() { return tenantId; }
    public String getCustomerId() { return customerId; }
    public String getSortCode() { return sortCode; }
    public String getAccountNumber() { return accountNumber; }
    public String getNickname() { return nickname; }
    public void setNickname(String nickname) { this.nickname = nickname; }
    public String getType() { return type; }
    public BigDecimal getBalance() { return balance; }
    public int getDailyLimit() { return dailyLimit; }
    public void setDailyLimit(int dailyLimit) { this.dailyLimit = dailyLimit; }
    /** Takes a payment off the balance held here. */
    public void debit(BigDecimal amount) { this.balance = this.balance.subtract(amount); }
    public Status getStatus() { return Status.valueOf(status); }
    public void setStatus(Status status) { this.status = status.name(); }
}
