package com.example.accounts.account;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** A support user looks after an account. Support users may only see accounts assigned to them. */
@Entity
@Table(name = "support_assignments")
public class SupportAssignment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String tenantId;

    @Column(nullable = false)
    private String supportUserId;

    @Column(nullable = false)
    private Long accountId;

    public Long getId() { return id; }
    public String getTenantId() { return tenantId; }
    public String getSupportUserId() { return supportUserId; }
    public Long getAccountId() { return accountId; }
}
