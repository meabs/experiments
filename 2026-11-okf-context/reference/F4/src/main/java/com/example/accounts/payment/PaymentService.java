package com.example.accounts.payment;

import java.math.BigDecimal;
import java.time.Clock;
import java.time.LocalDate;
import java.time.LocalDateTime;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.accounts.account.Account;
import com.example.accounts.account.AccountService;
import com.example.accounts.integration.fraud.Decision;
import com.example.accounts.integration.fraud.FraudScreeningClient;
import com.example.accounts.integration.fraud.FraudScreeningUnavailableException;
import com.example.accounts.integration.fraud.ScreeningRequest;
import com.example.accounts.integration.scheme.SchemeProperties;
import com.example.accounts.security.AccessPolicy;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ConflictException;
import com.example.accounts.web.ForbiddenException;
import com.example.accounts.web.NotFoundException;

@Service
@Transactional
public class PaymentService {

    private final PaymentRepository payments;
    private final AccountService accounts;
    private final PaymentDispatcher dispatcher;
    private final AccessPolicy access;
    private final CurrentUserProvider users;
    private final SchemeProperties scheme;
    private final Clock clock;
    private final FraudScreeningClient fraud;

    public PaymentService(PaymentRepository payments, AccountService accounts, PaymentDispatcher dispatcher,
                          AccessPolicy access, CurrentUserProvider users, SchemeProperties scheme, Clock clock,
                          FraudScreeningClient fraud) {
        this.fraud = fraud;
        this.payments = payments;
        this.accounts = accounts;
        this.dispatcher = dispatcher;
        this.access = access;
        this.users = users;
        this.scheme = scheme;
        this.clock = clock;
    }

    /** A payment out of the caller's own account. Only the account holder can pay from an account. */
    public Payment create(Long accountId, PaymentRequest req) {
        CurrentUser user = users.current();
        Account account = accounts.getVisible(accountId);
        if (!access.ownsAccount(user, account)) {
            throw new ForbiddenException("Only the account holder can make payments");
        }
        if (account.getStatus() != Account.Status.OPEN) {
            throw new ConflictException("Account is closed");
        }
        if (req.amount().compareTo(account.getBalance()) > 0) {
            throw new ConflictException("Insufficient funds");
        }
        if (paidToday(accountId).add(req.amount()).compareTo(BigDecimal.valueOf(account.getDailyLimit())) > 0) {
            throw new ConflictException("Daily limit exceeded");
        }
        Payment payment = payments.save(new Payment(account.getTenantId(), accountId, req.payeeName().trim(),
            req.payeeSortCode(), req.payeeAccountNumber(), req.amount(), req.reference(), user.id(), clock.instant()));

        Decision decision;
        try {
            decision = fraud.screen(new ScreeningRequest("P" + payment.getId(), account.getCustomerId(), accountId,
                payment.getPayeeName(), payment.getPayeeSortCode(), payment.getPayeeAccountNumber(), payment.getAmount()));
        } catch (FraudScreeningUnavailableException e) {
            decision = Decision.REFER; // fails closed: hold, never send unscreened
        }
        if (decision == Decision.REFER) {
            payment.setStatus(PaymentStatus.HELD_FOR_REVIEW);
            return payments.save(payment);
        }
        if (decision == Decision.REJECT) {
            payment.setStatus(PaymentStatus.REJECTED);
            payment.setReasonCode("FRAUD");
            return payments.save(payment);
        }

        LocalDateTime now = LocalDateTime.now(clock);
        if (!WorkingDays.isWorkingDay(now.toLocalDate()) || now.toLocalTime().isAfter(scheme.cutoff())) {
            LocalDate next = WorkingDays.next(now.toLocalDate());
            payment.setStatus(PaymentStatus.QUEUED);
            payment.setExecutionDate(next);
            return payments.save(payment);
        }
        return dispatcher.dispatch(payment);
    }

    @Transactional(readOnly = true)
    public Payment get(Long paymentId) {
        Payment payment = payments.findById(paymentId).orElseThrow(() -> new NotFoundException("Payment not found"));
        try {
            accounts.getVisible(payment.getAccountId());
        } catch (NotFoundException e) {
            throw new NotFoundException("Payment not found");
        }
        return payment;
    }

    private BigDecimal paidToday(Long accountId) {
        return payments.findByAccountIdAndCreatedAtGreaterThanEqual(accountId,
                LocalDate.now(clock).atStartOfDay(clock.getZone()).toInstant()).stream()
            .filter(p -> p.getStatus() != PaymentStatus.REJECTED && p.getStatus() != PaymentStatus.CANCELLED)
            .map(Payment::getAmount).reduce(BigDecimal.ZERO, BigDecimal::add);
    }
}
