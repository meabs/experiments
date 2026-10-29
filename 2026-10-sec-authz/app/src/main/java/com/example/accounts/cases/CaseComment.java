package com.example.accounts.cases;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** A comment on a case. Internal comments are between staff and are never shown to the customer. */
@Entity
@Table(name = "case_comments")
public class CaseComment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String caseId;

    @Column(nullable = false)
    private String author;

    @Column(nullable = false, length = 2000)
    private String body;

    @Column(nullable = false)
    private boolean internal;

    @Column(nullable = false)
    private Instant createdAt;

    public Long getId() { return id; }
    public String getCaseId() { return caseId; }
    public String getAuthor() { return author; }
    public String getBody() { return body; }
    public boolean isInternal() { return internal; }
    public Instant getCreatedAt() { return createdAt; }
}
