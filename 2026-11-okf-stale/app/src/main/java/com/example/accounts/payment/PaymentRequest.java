package com.example.accounts.payment;

import java.math.BigDecimal;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Digits;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record PaymentRequest(
    @NotBlank @Size(max = 70) String payeeName,
    @NotNull @Pattern(regexp = "\\d{6}") String payeeSortCode,
    @NotNull @Pattern(regexp = "\\d{8}") String payeeAccountNumber,
    @NotNull @DecimalMin("0.01") @Digits(integer = 7, fraction = 2) BigDecimal amount,
    @Size(max = 18) String reference) {
}
