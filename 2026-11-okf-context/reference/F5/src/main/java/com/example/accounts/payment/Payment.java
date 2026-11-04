package com.example.accounts.payment;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "payments")
public class Payment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String tenantId;

    @Column(nullable = false)
    private Long accountId;

    @Column(nullable = false)
    private String payeeName;

    @Column(nullable = false)
    private String payeeSortCode;

    @Column(nullable = false)
    private String payeeAccountNumber;

    @Column(nullable = false)
    private BigDecimal amount;

    /** The customer's reference, shown on the payee's statement. */
    private String reference;

    @Column(nullable = false)
    private String status;

    /** Reason code when the scheme rejected the payment. */
    private String reasonCode;

    private LocalDate executionDate;

    /** Id the scheme gave the instruction. */
    private String schemeId;

    /** Reference sent with the ledger posting. */
    private String ledgerReference;

    /** Automatic ledger reposts tried so far. */
    private Integer ledgerRetries;

    @Column(nullable = false)
    private String createdBy;

    @Column(nullable = false)
    private Instant createdAt;

    protected Payment() {
    }

    public Payment(String tenantId, Long accountId, String payeeName, String payeeSortCode, String payeeAccountNumber,
                   BigDecimal amount, String reference, String createdBy, Instant createdAt) {
        this.tenantId = tenantId;
        this.accountId = accountId;
        this.payeeName = payeeName;
        this.payeeSortCode = payeeSortCode;
        this.payeeAccountNumber = payeeAccountNumber;
        this.amount = amount;
        this.reference = reference;
        this.createdBy = createdBy;
        this.createdAt = createdAt;
        this.status = PaymentStatus.RECEIVED.name();
    }

    public Long getId() { return id; }
    public String getTenantId() { return tenantId; }
    public Long getAccountId() { return accountId; }
    public String getPayeeName() { return payeeName; }
    public String getPayeeSortCode() { return payeeSortCode; }
    public String getPayeeAccountNumber() { return payeeAccountNumber; }
    public BigDecimal getAmount() { return amount; }
    public String getReference() { return reference; }
    public PaymentStatus getStatus() { return PaymentStatus.valueOf(status); }
    public void setStatus(PaymentStatus status) { this.status = status.name(); }
    public String getReasonCode() { return reasonCode; }
    public void setReasonCode(String reasonCode) { this.reasonCode = reasonCode; }
    public LocalDate getExecutionDate() { return executionDate; }
    public void setExecutionDate(LocalDate executionDate) { this.executionDate = executionDate; }
    public String getSchemeId() { return schemeId; }
    public void setSchemeId(String schemeId) { this.schemeId = schemeId; }
    public String getLedgerReference() { return ledgerReference; }
    public void setLedgerReference(String ledgerReference) { this.ledgerReference = ledgerReference; }
    public int getLedgerRetries() { return ledgerRetries == null ? 0 : ledgerRetries; }
    public void setLedgerRetries(int ledgerRetries) { this.ledgerRetries = ledgerRetries; }
    public String getCreatedBy() { return createdBy; }
    public Instant getCreatedAt() { return createdAt; }
}
