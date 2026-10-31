package com.example.accounts.account;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.account.AccountController.AccountView;
import com.example.accounts.security.AccessPolicy;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ConflictException;
import com.example.accounts.web.ForbiddenException;

/**
 * Changing an account's daily limit. Admins set any limit up to 5000; assigned support can only lower it. Savings
 * accounts' limits are fixed. Every change leaves an internal note with the old and new limit.
 */
@RestController
public class DailyLimitController {

    public static final int CEILING = 5000;

    public record Limit(Integer dailyLimit) {
    }

    private final AccountService accounts;
    private final AccountRepository repo;
    private final AccountNoteRepository notes;
    private final AccessPolicy access;
    private final CurrentUserProvider users;

    public DailyLimitController(AccountService accounts, AccountRepository repo, AccountNoteRepository notes,
                                AccessPolicy access, CurrentUserProvider users) {
        this.accounts = accounts;
        this.repo = repo;
        this.notes = notes;
        this.access = access;
        this.users = users;
    }

    @PutMapping("/api/accounts/{accountId}/daily-limit")
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    @Transactional
    public AccountView set(@PathVariable Long accountId, @RequestBody Limit body) {
        CurrentUser user = users.current();
        Account account = accounts.getVisible(accountId);
        boolean admin = access.isTenantAdmin(user, account.getTenantId());
        if (!admin && !access.isAssignedSupport(user, account)) {
            throw new ForbiddenException("Only staff can change the daily limit");
        }
        if (body.dailyLimit() == null || body.dailyLimit() < 0 || body.dailyLimit() > CEILING) {
            throw new IllegalArgumentException("dailyLimit must be 0 to " + CEILING);
        }
        int old = account.getDailyLimit();
        if (!admin && body.dailyLimit() > old) {
            throw new ForbiddenException("Only admins can raise a daily limit");
        }
        if (account.getStatus() == Account.Status.CLOSED || "SAVINGS".equals(account.getType())) {
            throw new ConflictException("This account's daily limit can't be changed");
        }
        account.setDailyLimit(body.dailyLimit());
        repo.save(account);
        notes.save(new AccountNote(account.getId(), user.id(),
            "Daily limit changed from " + old + " to " + body.dailyLimit(), true));
        return AccountView.of(account);
    }
}
