package com.example.accounts.payment;

import java.time.Clock;
import java.time.LocalDate;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/** Sends queued payments on their execution date, each working day at 06:00. */
@Component
public class QueuedPaymentJob {

    private final PaymentRepository payments;
    private final PaymentDispatcher dispatcher;
    private final Clock clock;

    public QueuedPaymentJob(PaymentRepository payments, PaymentDispatcher dispatcher, Clock clock) {
        this.payments = payments;
        this.dispatcher = dispatcher;
        this.clock = clock;
    }

    @Scheduled(cron = "0 0 6 * * MON-FRI", zone = "Europe/London")
    @Transactional
    public void runDue() {
        for (Payment p : payments.findByStatusAndExecutionDateLessThanEqualOrderById(PaymentStatus.QUEUED.name(),
                LocalDate.now(clock))) {
            dispatcher.dispatch(p);
        }
    }
}
