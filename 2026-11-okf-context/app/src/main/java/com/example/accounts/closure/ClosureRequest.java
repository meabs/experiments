package com.example.accounts.closure;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** A request to close an account. Closing needs a second person, an approver, to approve the request. */
@Entity
@Table(name = "closure_requests")
public class ClosureRequest {

    public enum Status { PENDING, APPROVED, REJECTED }

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String tenantId;

    @Column(nullable = false)
    private Long accountId;

    /** User id of whoever raised the request. */
    @Column(nullable = false)
    private String requestedBy;

    @Column(nullable = false)
    private String status;

    private String decidedBy;
    private Instant decidedAt;

    @Column(nullable = false)
    private Instant requestedAt;

    protected ClosureRequest() {
    }

    public ClosureRequest(String tenantId, Long accountId, String requestedBy) {
        this.tenantId = tenantId;
        this.accountId = accountId;
        this.requestedBy = requestedBy;
        this.status = Status.PENDING.name();
        this.requestedAt = Instant.now();
    }

    public Long getId() { return id; }
    public String getTenantId() { return tenantId; }
    public Long getAccountId() { return accountId; }
    public String getRequestedBy() { return requestedBy; }
    public Status getStatus() { return Status.valueOf(status); }
    public void setStatus(Status status) { this.status = status.name(); }
    public String getDecidedBy() { return decidedBy; }
    public void setDecidedBy(String decidedBy) { this.decidedBy = decidedBy; }
    public Instant getDecidedAt() { return decidedAt; }
    public void setDecidedAt(Instant decidedAt) { this.decidedAt = decidedAt; }
    public Instant getRequestedAt() { return requestedAt; }
}
