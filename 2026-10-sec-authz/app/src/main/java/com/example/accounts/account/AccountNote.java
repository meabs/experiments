package com.example.accounts.account;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * A note on an account, written by staff. Internal notes ({@code internal = true}) are for staff only: they can record
 * fraud checks, hardship and similar, and must never be shown to the customer.
 */
@Entity
@Table(name = "account_notes")
public class AccountNote {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Long accountId;

    @Column(nullable = false)
    private String author;

    @Column(nullable = false, length = 2000)
    private String body;

    @Column(nullable = false)
    private boolean internal;

    @Column(nullable = false)
    private Instant createdAt;

    public Long getId() { return id; }
    public Long getAccountId() { return accountId; }
    public String getAuthor() { return author; }
    public String getBody() { return body; }
    public boolean isInternal() { return internal; }
    public Instant getCreatedAt() { return createdAt; }
}
