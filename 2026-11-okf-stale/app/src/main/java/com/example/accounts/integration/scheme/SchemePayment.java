package com.example.accounts.integration.scheme;

import java.math.BigDecimal;
import java.time.LocalDate;

/** A payment instruction as the scheme gateway takes it. */
public record SchemePayment(String reference, String fromSortCode, String fromAccountNumber, String payeeName,
                            String payeeSortCode, String payeeAccountNumber, BigDecimal amount, String customerReference,
                            LocalDate executionDate) {
}
