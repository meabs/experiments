package com.example.accounts.support;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.example.accounts.integration.ledger.LedgerClient;
import com.example.accounts.integration.ledger.LedgerPosting;
import com.example.accounts.integration.ledger.LedgerTimeoutException;

/**
 * Behaves like the core ledger: {@link #applied} holds each posting the ledger has booked, keyed by reference; a second
 * posting with a reference already booked is not booked again. {@link #calls} records every call.
 * {@link #timeOutNext(int, boolean)} makes the next calls time out, either before or after the ledger books them.
 */
public class FakeLedger implements LedgerClient {

    public final Map<String, LedgerPosting> applied = new LinkedHashMap<>();
    public final List<LedgerPosting> calls = new ArrayList<>();
    private int timeouts;
    private boolean applyBeforeTimeout;

    public void reset() {
        applied.clear();
        calls.clear();
        timeouts = 0;
        applyBeforeTimeout = false;
    }

    public void timeOutNext(int count, boolean applyBeforeTimeout) {
        this.timeouts = count;
        this.applyBeforeTimeout = applyBeforeTimeout;
    }

    /** Postings booked for an account, oldest first. */
    public List<LedgerPosting> bookedFor(Long accountId) {
        return applied.values().stream().filter(p -> p.accountId().equals(accountId)).toList();
    }

    @Override
    public synchronized void post(LedgerPosting posting) {
        calls.add(posting);
        if (timeouts > 0) {
            timeouts--;
            if (applyBeforeTimeout) {
                applied.putIfAbsent(posting.reference(), posting);
            }
            throw new LedgerTimeoutException("timed out", null);
        }
        applied.putIfAbsent(posting.reference(), posting);
    }
}
