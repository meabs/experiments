package com.example.accounts.payment;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/** Retries the ledger posting of POSTING_FAILED payments every 15 minutes, at most 3 times each. */
@Component
public class LedgerRetryJob {

    static final int MAX_RETRIES = 3;

    private final PaymentRepository payments;
    private final PaymentDispatcher dispatcher;

    public LedgerRetryJob(PaymentRepository payments, PaymentDispatcher dispatcher) {
        this.payments = payments;
        this.dispatcher = dispatcher;
    }

    @Scheduled(fixedDelay = 15, timeUnit = java.util.concurrent.TimeUnit.MINUTES, initialDelay = 15)
    @Transactional
    public void retryFailed() {
        for (Payment p : payments.findByStatusOrderById(PaymentStatus.POSTING_FAILED.name())) {
            if (p.getLedgerRetries() >= MAX_RETRIES) {
                continue;
            }
            p.setLedgerRetries(p.getLedgerRetries() + 1);
            dispatcher.repost(p);
            payments.save(p);
        }
    }
}
