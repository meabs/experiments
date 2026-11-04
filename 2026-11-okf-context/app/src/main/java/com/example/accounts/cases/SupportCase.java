package com.example.accounts.cases;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * A support case raised by a customer about one of their accounts, handled by one support user (the assignee). Note that
 * the case assignee is not the same thing as the support users assigned to the account.
 */
@Entity
@Table(name = "support_cases")
public class SupportCase {

    @Id
    private String id;

    @Column(nullable = false)
    private String tenantId;

    @Column(nullable = false)
    private Long accountId;

    @Column(nullable = false)
    private String customerId;

    @Column(nullable = false)
    private String subject;

    @Column(nullable = false)
    private String status;

    /** User id of the support user handling the case; null until someone picks it up. */
    private String assigneeUserId;

    @Column(nullable = false)
    private Instant openedAt;

    protected SupportCase() {
    }

    public SupportCase(String id, String tenantId, Long accountId, String customerId, String subject) {
        this.id = id;
        this.tenantId = tenantId;
        this.accountId = accountId;
        this.customerId = customerId;
        this.subject = subject;
        this.status = "OPEN";
        this.openedAt = Instant.now();
    }

    public String getId() { return id; }
    public String getTenantId() { return tenantId; }
    public Long getAccountId() { return accountId; }
    public String getCustomerId() { return customerId; }
    public String getSubject() { return subject; }
    public String getStatus() { return status; }
    public String getAssigneeUserId() { return assigneeUserId; }
    public Instant getOpenedAt() { return openedAt; }
}
