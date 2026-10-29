package com.example.accounts.account;

import java.util.Map;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.security.AccessPolicy;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ConflictException;
import com.example.accounts.web.ForbiddenException;

@RestController
public class AccountSettingsController {

    private final AccountService accounts;
    private final AccessPolicy access;
    private final CurrentUserProvider users;

    public AccountSettingsController(AccountService accounts, AccessPolicy access, CurrentUserProvider users) {
        this.accounts = accounts;
        this.access = access;
        this.users = users;
    }

    @PatchMapping("/api/accounts/{accountId}")
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    @Transactional
    public AccountController.AccountView update(@PathVariable Long accountId, @RequestBody Map<String, Object> body) {
        CurrentUser user = users.current();
        Account account = accounts.getVisible(accountId); // 404 unless the caller may see it
        if (account.getStatus() == Account.Status.CLOSED) {
            throw new ConflictException("Account is closed");
        }
        boolean admin = access.isTenantAdmin(user, account.getTenantId());
        boolean owner = access.ownsAccount(user, account) || access.isAssignedSupport(user, account);
        boolean wantsLimit = body.containsKey("dailyLimit");
        boolean wantsNickname = body.containsKey("nickname");
        if (!admin && !(owner && !wantsLimit)) {
            throw new ForbiddenException(owner ? "Only the bank can change the daily limit" : "Not allowed");
        }
        if (!wantsLimit && !wantsNickname) {
            throw new IllegalArgumentException("Nothing to change");
        }
        String nickname = null;
        Integer limit = null;
        if (wantsNickname) {
            if (!(body.get("nickname") instanceof String s) || s.trim().isEmpty() || s.trim().length() > 40) {
                throw new IllegalArgumentException("nickname must be 1 to 40 characters");
            }
            nickname = s.trim();
        }
        if (wantsLimit) {
            if (!(body.get("dailyLimit") instanceof Integer n) || n < 0 || n > 5000) {
                throw new IllegalArgumentException("dailyLimit must be a whole number from 0 to 5000");
            }
            limit = n;
        }
        if (nickname != null) {
            account.setNickname(nickname);
        }
        if (limit != null) {
            account.setDailyLimit(limit);
        }
        return AccountController.AccountView.of(account);
    }
}
