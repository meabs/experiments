package com.example.accounts.payment;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/** Resubmits payments whose scheme submission timed out, every 5 minutes, under their original reference. */
@Component
public class SchemeRetryJob {

    private final PaymentRepository payments;
    private final PaymentDispatcher dispatcher;

    public SchemeRetryJob(PaymentRepository payments, PaymentDispatcher dispatcher) {
        this.payments = payments;
        this.dispatcher = dispatcher;
    }

    @Scheduled(fixedDelay = 5, timeUnit = java.util.concurrent.TimeUnit.MINUTES, initialDelay = 5)
    @Transactional
    public void resubmit() {
        for (Payment p : payments.findByStatusOrderById(PaymentStatus.RECEIVED.name())) {
            dispatcher.dispatch(p, true);
        }
    }
}
