package com.example.accounts.integration.ledger;

/** Posts entries to the core banking ledger. */
public interface LedgerClient {

    /** @throws LedgerTimeoutException if the ledger does not answer in time */
    void post(LedgerPosting posting);
}
