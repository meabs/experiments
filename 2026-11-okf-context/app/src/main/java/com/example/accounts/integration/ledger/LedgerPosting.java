package com.example.accounts.integration.ledger;

import java.math.BigDecimal;

/**
 * One posting to the core ledger. {@code amount} is negative for a debit. {@code reference} is sent with the posting.
 */
public record LedgerPosting(String reference, Long accountId, BigDecimal amount, String narrative) {
}
