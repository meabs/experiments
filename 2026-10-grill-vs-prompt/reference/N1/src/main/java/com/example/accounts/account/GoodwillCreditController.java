package com.example.accounts.account;

import java.math.BigDecimal;
import java.time.Instant;

import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.security.AccessPolicy;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ConflictException;
import com.example.accounts.web.ForbiddenException;
import com.example.accounts.web.NotFoundException;

/** Goodwill credits: up to £100 paid at once; more waits for an approver who didn't ask for it. */
@RestController
public class GoodwillCreditController {

    static final BigDecimal THRESHOLD = new BigDecimal("100");

    public record NewCredit(BigDecimal amount, String reason) {
    }

    public record CreditView(Long id, Long accountId, BigDecimal amount, String reason, String status, String createdBy,
                             Instant createdAt) {
        static CreditView of(GoodwillCredit c) {
            return new CreditView(c.getId(), c.getAccountId(), c.getAmount(), c.getReason(), c.getStatus(), c.getCreatedBy(),
                c.getCreatedAt());
        }
    }

    private final AccountService accounts;
    private final AccountRepository repo;
    private final TransactionRepository transactions;
    private final GoodwillCreditRepository credits;
    private final AccessPolicy access;
    private final CurrentUserProvider users;

    public GoodwillCreditController(AccountService accounts, AccountRepository repo, TransactionRepository transactions,
                                    GoodwillCreditRepository credits, AccessPolicy access, CurrentUserProvider users) {
        this.accounts = accounts;
        this.repo = repo;
        this.transactions = transactions;
        this.credits = credits;
        this.access = access;
        this.users = users;
    }

    @PostMapping("/api/accounts/{accountId}/goodwill-credits")
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    @ResponseStatus(HttpStatus.CREATED)
    @Transactional
    public CreditView create(@PathVariable Long accountId, @RequestBody NewCredit body) {
        CurrentUser user = users.current();
        Account account = accounts.getVisible(accountId);
        if (!access.isTenantAdmin(user, account.getTenantId()) && !access.isAssignedSupport(user, account)) {
            throw new ForbiddenException("Only staff who look after the account can give a goodwill credit");
        }
        BigDecimal amount = body.amount();
        String reason = body.reason() == null ? "" : body.reason().trim();
        if (amount == null || amount.signum() <= 0 || amount.stripTrailingZeros().scale() > 2
            || reason.isEmpty() || reason.length() > 500) {
            throw new IllegalArgumentException("amount must be more than 0 with at most 2 decimals; reason 1 to 500 characters");
        }
        boolean pending = amount.compareTo(THRESHOLD) > 0;
        GoodwillCredit c = credits.save(new GoodwillCredit(account.getTenantId(), accountId, amount, reason,
            pending ? "PENDING" : "PAID", user.id()));
        if (!pending) {
            pay(account, amount);
        }
        return CreditView.of(c);
    }

    @PostMapping("/api/goodwill-credits/{creditId}/approve")
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    @Transactional
    public CreditView approve(@PathVariable Long creditId) {
        CurrentUser user = users.current();
        GoodwillCredit c = credits.findById(creditId).filter(x -> user.inTenant(x.getTenantId()))
            .orElseThrow(() -> new NotFoundException("Credit not found"));
        if (!user.hasRole(CurrentUser.APPROVER)) {
            throw new ForbiddenException("Only approvers can approve a goodwill credit");
        }
        if (user.id().equals(c.getCreatedBy())) {
            throw new ForbiddenException("You can't approve a credit you asked for");
        }
        if (!"PENDING".equals(c.getStatus())) {
            throw new ConflictException("Credit is not pending");
        }
        pay(repo.findById(c.getAccountId()).orElseThrow(), c.getAmount());
        c.setStatus("PAID");
        c.setApprovedBy(user.id());
        return CreditView.of(c);
    }

    private void pay(Account account, BigDecimal amount) {
        account.setBalance(account.getBalance().add(amount));
        repo.save(account);
        transactions.save(new Transaction(account.getId(), amount, "Goodwill credit"));
    }
}
