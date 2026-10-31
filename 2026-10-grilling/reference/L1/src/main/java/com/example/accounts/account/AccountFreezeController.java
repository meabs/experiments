package com.example.accounts.account;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.account.AccountController.AccountView;
import com.example.accounts.security.AccessPolicy;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ConflictException;
import com.example.accounts.web.ForbiddenException;

/**
 * Freezing an account while fraud is looked into. Staff who look after the account can freeze it; only admins can lift
 * a freeze. Each freeze and unfreeze leaves an internal note as an audit trail.
 */
@RestController
public class AccountFreezeController {

    public record Reason(String reason) {
    }

    private final AccountService accounts;
    private final AccountRepository repo;
    private final AccountNoteRepository notes;
    private final AccessPolicy access;
    private final CurrentUserProvider users;

    public AccountFreezeController(AccountService accounts, AccountRepository repo, AccountNoteRepository notes,
                                   AccessPolicy access, CurrentUserProvider users) {
        this.accounts = accounts;
        this.repo = repo;
        this.notes = notes;
        this.access = access;
        this.users = users;
    }

    @PostMapping("/api/accounts/{accountId}/freeze")
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    @Transactional
    public AccountView freeze(@PathVariable Long accountId, @RequestBody Reason body) {
        CurrentUser user = users.current();
        Account account = accounts.getVisible(accountId);
        if (!access.isTenantAdmin(user, account.getTenantId()) && !access.isAssignedSupport(user, account)) {
            throw new ForbiddenException("Only staff can freeze accounts");
        }
        String reason = reason(body.reason());
        if (account.getStatus() != Account.Status.OPEN) {
            throw new ConflictException("Only an open account can be frozen");
        }
        account.setStatus(Account.Status.FROZEN);
        repo.save(account);
        notes.save(new AccountNote(account.getId(), user.id(), "Account frozen: " + reason, true));
        return AccountView.of(account);
    }

    @PostMapping("/api/accounts/{accountId}/unfreeze")
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    @Transactional
    public AccountView unfreeze(@PathVariable Long accountId) {
        CurrentUser user = users.current();
        Account account = accounts.getVisible(accountId);
        if (!access.isTenantAdmin(user, account.getTenantId())) {
            throw new ForbiddenException("Only admins can lift a freeze");
        }
        if (account.getStatus() != Account.Status.FROZEN) {
            throw new ConflictException("Only a frozen account can be unfrozen");
        }
        account.setStatus(Account.Status.OPEN);
        repo.save(account);
        notes.save(new AccountNote(account.getId(), user.id(), "Freeze lifted", true));
        return AccountView.of(account);
    }

    public static String reason(String s) {
        String r = s == null ? "" : s.trim();
        if (r.isEmpty() || r.length() > 500) {
            throw new IllegalArgumentException("reason must be 1 to 500 characters");
        }
        return r;
    }
}
