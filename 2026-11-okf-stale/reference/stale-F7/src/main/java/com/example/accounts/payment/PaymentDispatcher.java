package com.example.accounts.payment;

import java.time.Clock;
import java.time.LocalDate;
import java.util.Map;
import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import com.example.accounts.account.Account;
import com.example.accounts.account.AccountRepository;
import com.example.accounts.customer.CustomerRepository;
import com.example.accounts.integration.ledger.LedgerClient;
import com.example.accounts.integration.ledger.LedgerPosting;
import com.example.accounts.integration.ledger.LedgerTimeoutException;
import com.example.accounts.integration.notify.Notification;
import com.example.accounts.integration.notify.NotificationClient;
import com.example.accounts.integration.scheme.SchemeClient;
import com.example.accounts.integration.scheme.SchemePayment;
import com.example.accounts.integration.scheme.SchemeReceipt;
import com.example.accounts.integration.scheme.SchemeRejectedException;

/** Sends a payment to the scheme, posts it to the ledger and tells the customer. */
@Component
public class PaymentDispatcher {

    private static final Logger log = LoggerFactory.getLogger(PaymentDispatcher.class);

    private final SchemeClient scheme;
    private final LedgerClient ledger;
    private final NotificationClient notifications;
    private final AccountRepository accounts;
    private final CustomerRepository customers;
    private final PaymentRepository payments;
    private final Clock clock;

    public PaymentDispatcher(SchemeClient scheme, LedgerClient ledger, NotificationClient notifications,
                             AccountRepository accounts, CustomerRepository customers, PaymentRepository payments,
                             Clock clock) {
        this.scheme = scheme;
        this.ledger = ledger;
        this.notifications = notifications;
        this.accounts = accounts;
        this.customers = customers;
        this.payments = payments;
        this.clock = clock;
    }

    public Payment dispatch(Payment payment) {
        Account account = accounts.findById(payment.getAccountId()).orElseThrow();
        LocalDate today = LocalDate.now(clock);
        try {
            SchemeReceipt receipt = scheme.submit(new SchemePayment("P" + payment.getId(), account.getSortCode(),
                account.getAccountNumber(), payment.getPayeeName(), payment.getPayeeSortCode(),
                payment.getPayeeAccountNumber(), payment.getAmount(), payment.getReference(), today));
            payment.setSchemeId(receipt.schemeId());
            payment.setExecutionDate(today);
            payment.setStatus(PaymentStatus.SUBMITTED);
        } catch (SchemeRejectedException e) {
            payment.setStatus(PaymentStatus.REJECTED);
            payment.setReasonCode(e.getCode());
            payments.save(payment);
            notify(account, payment, "PAYMENT_DECLINED");
            return payment;
        }
        account.debit(payment.getAmount());
        payment.setLedgerReference(UUID.randomUUID().toString());
        try {
            ledger.post(new LedgerPosting(payment.getLedgerReference(), account.getId(), payment.getAmount().negate(),
                "Payment to " + payment.getPayeeName()));
            payment.setStatus(PaymentStatus.COMPLETED);
        } catch (LedgerTimeoutException e) {
            log.warn("Ledger posting failed for payment {}", payment.getId(), e);
            payment.setStatus(PaymentStatus.POSTING_FAILED);
        }
        payments.save(payment);
        notify(account, payment, "PAYMENT_SENT");
        return payment;
    }

    /** Tells the customer about the payment (best effort). Last four digits of the account only. */
    public void notify(Account account, Payment payment, String template) {
        try {
            customers.findById(account.getCustomerId()).ifPresent(c -> notifications.send(new Notification(c.getUserId(),
                template, Map.of("amount", payment.getAmount().toPlainString(), "payee", payment.getPayeeName(),
                    "accountEnding", account.getAccountNumber().substring(4)))));
        } catch (RuntimeException e) {
            log.warn("Could not notify customer of payment {}", payment.getId(), e);
        }
    }
}
