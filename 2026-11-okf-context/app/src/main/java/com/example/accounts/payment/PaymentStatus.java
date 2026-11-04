package com.example.accounts.payment;

public enum PaymentStatus {
    RECEIVED,
    /** Waiting for its execution date; sent by {@link QueuedPaymentJob}. */
    QUEUED,
    SUBMITTED,
    COMPLETED,
    /** Sent to the scheme, but the ledger posting failed. */
    POSTING_FAILED,
    HELD_FOR_REVIEW,
    REJECTED,
    CANCELLED
}
