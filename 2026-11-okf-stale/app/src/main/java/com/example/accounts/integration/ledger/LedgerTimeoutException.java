package com.example.accounts.integration.ledger;

/** The ledger did not answer within the configured timeout. */
public class LedgerTimeoutException extends RuntimeException {

    public LedgerTimeoutException(String message, Throwable cause) {
        super(message, cause);
    }
}
