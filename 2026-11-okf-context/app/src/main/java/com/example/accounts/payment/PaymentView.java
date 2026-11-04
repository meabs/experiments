package com.example.accounts.payment;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;

public record PaymentView(Long id, Long accountId, String payeeName, String payeeSortCode, String payeeAccountNumber,
                          BigDecimal amount, String reference, String status, String reasonCode,
                          LocalDate executionDate, Instant createdAt) {

    static PaymentView of(Payment p) {
        return new PaymentView(p.getId(), p.getAccountId(), p.getPayeeName(), p.getPayeeSortCode(),
            p.getPayeeAccountNumber(), p.getAmount(), p.getReference(), p.getStatus().name(), p.getReasonCode(),
            p.getExecutionDate(), p.getCreatedAt());
    }
}
