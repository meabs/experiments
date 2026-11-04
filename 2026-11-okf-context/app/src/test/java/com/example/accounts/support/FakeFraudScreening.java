package com.example.accounts.support;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

import com.example.accounts.integration.fraud.Decision;
import com.example.accounts.integration.fraud.FraudScreeningClient;
import com.example.accounts.integration.fraud.FraudScreeningUnavailableException;
import com.example.accounts.integration.fraud.ScreeningRequest;

/**
 * Answers {@code ACCEPT} unless told otherwise. {@link #answer(Decision...)} queues answers for the next calls;
 * {@link #unavailable()} makes the next call fail as a timeout does.
 */
public class FakeFraudScreening implements FraudScreeningClient {

    public final List<ScreeningRequest> requests = new ArrayList<>();
    private final Deque<Object> next = new ArrayDeque<>();

    public void reset() {
        requests.clear();
        next.clear();
    }

    public void answer(Decision... decisions) {
        for (Decision d : decisions) {
            next.add(d);
        }
    }

    public void unavailable() {
        next.add("UNAVAILABLE");
    }

    @Override
    public synchronized Decision screen(ScreeningRequest request) {
        requests.add(request);
        Object n = next.poll();
        if ("UNAVAILABLE".equals(n)) {
            throw new FraudScreeningUnavailableException("timed out", null);
        }
        return n == null ? Decision.ACCEPT : (Decision) n;
    }
}
