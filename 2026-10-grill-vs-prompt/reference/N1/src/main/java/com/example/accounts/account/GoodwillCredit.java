package com.example.accounts.account;

import java.math.BigDecimal;
import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "goodwill_credits")
public class GoodwillCredit {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String tenantId;

    @Column(nullable = false)
    private Long accountId;

    @Column(nullable = false)
    private BigDecimal amount;

    @Column(nullable = false, length = 500)
    private String reason;

    @Column(nullable = false)
    private String status;

    @Column(nullable = false)
    private String createdBy;

    private String approvedBy;

    @Column(nullable = false)
    private Instant createdAt;

    protected GoodwillCredit() {
    }

    public GoodwillCredit(String tenantId, Long accountId, BigDecimal amount, String reason, String status, String createdBy) {
        this.tenantId = tenantId;
        this.accountId = accountId;
        this.amount = amount;
        this.reason = reason;
        this.status = status;
        this.createdBy = createdBy;
        this.createdAt = Instant.now();
    }

    public Long getId() { return id; }
    public String getTenantId() { return tenantId; }
    public Long getAccountId() { return accountId; }
    public BigDecimal getAmount() { return amount; }
    public String getReason() { return reason; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getCreatedBy() { return createdBy; }
    public String getApprovedBy() { return approvedBy; }
    public void setApprovedBy(String approvedBy) { this.approvedBy = approvedBy; }
    public Instant getCreatedAt() { return createdAt; }
}
