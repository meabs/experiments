package com.example.accounts.support;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.example.accounts.integration.scheme.SchemeClient;
import com.example.accounts.integration.scheme.SchemePayment;
import com.example.accounts.integration.scheme.SchemeReceipt;
import com.example.accounts.integration.scheme.SchemeRejectedException;
import com.example.accounts.integration.scheme.SchemeTimeoutException;

/**
 * Behaves like the scheme gateway: {@link #accepted} holds each instruction the scheme has taken, keyed by reference,
 * and a reference it has already taken is rejected with reason code DUPL. {@link #submitted} lists the accepted
 * instructions in order; {@link #calls} records every call. {@link #rejectNext(String)} makes the next submission fail
 * with that reason code; {@link #timeOutNext(boolean)} makes it time out, either before or after the scheme takes it.
 */
public class FakeScheme implements SchemeClient {

    public final List<SchemePayment> submitted = new ArrayList<>();
    public final Map<String, SchemePayment> accepted = new LinkedHashMap<>();
    public final List<SchemePayment> calls = new ArrayList<>();
    private String rejectCode;
    private Boolean timeout; // null: none; false: before accepting; true: after accepting

    public void reset() {
        submitted.clear();
        accepted.clear();
        calls.clear();
        rejectCode = null;
        timeout = null;
    }

    public void rejectNext(String code) {
        this.rejectCode = code;
    }

    public void timeOutNext(boolean acceptedBeforeTimeout) {
        this.timeout = acceptedBeforeTimeout;
    }

    @Override
    public synchronized SchemeReceipt submit(SchemePayment payment) {
        calls.add(payment);
        if (rejectCode != null) {
            String code = rejectCode;
            rejectCode = null;
            throw new SchemeRejectedException(code, "rejected");
        }
        if (accepted.containsKey(payment.reference())) {
            throw new SchemeRejectedException("DUPL", "duplicate reference");
        }
        Boolean t = timeout;
        timeout = null;
        if (Boolean.FALSE.equals(t)) {
            throw new SchemeTimeoutException("timed out", null);
        }
        accepted.put(payment.reference(), payment);
        submitted.add(payment);
        if (Boolean.TRUE.equals(t)) {
            throw new SchemeTimeoutException("timed out", null);
        }
        return new SchemeReceipt("S-" + (100000 + submitted.size()));
    }
}
