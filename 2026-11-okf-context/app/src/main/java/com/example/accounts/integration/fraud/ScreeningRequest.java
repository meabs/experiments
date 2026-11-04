package com.example.accounts.integration.fraud;

import java.math.BigDecimal;

public record ScreeningRequest(String paymentReference, String customerId, Long accountId, String payeeName,
                               String payeeSortCode, String payeeAccountNumber, BigDecimal amount) {
}
