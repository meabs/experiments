package com.example.accounts.closure;

import java.time.Instant;
import java.util.List;

import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.ResponseStatus;

import com.example.accounts.account.Account;
import com.example.accounts.account.AccountService;
import com.example.accounts.security.AccessPolicy;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ConflictException;
import com.example.accounts.web.ForbiddenException;

@RestController
public class ClosureController {

    public record ClosureView(Long id, Long accountId, String requestedBy, String status, String decidedBy,
                              Instant requestedAt) {
        static ClosureView of(ClosureRequest r) {
            return new ClosureView(r.getId(), r.getAccountId(), r.getRequestedBy(), r.getStatus().name(), r.getDecidedBy(),
                r.getRequestedAt());
        }
    }

    private final ClosureRequestRepository requests;
    private final AccountService accounts;
    private final AccessPolicy access;
    private final CurrentUserProvider users;

    public ClosureController(ClosureRequestRepository requests, AccountService accounts, AccessPolicy access,
                             CurrentUserProvider users) {
        this.requests = requests;
        this.accounts = accounts;
        this.access = access;
        this.users = users;
    }

    /** The account holder or an admin of the account's tenant asks for the account to be closed. */
    @PostMapping("/api/accounts/{accountId}/closure-requests")
    @ResponseStatus(HttpStatus.CREATED)
    @Transactional
    public ClosureView request(@PathVariable Long accountId) {
        CurrentUser user = users.current();
        Account account = accounts.getVisible(accountId); // 404 unless the caller may see it
        if (!access.ownsAccount(user, account) && !access.isTenantAdmin(user, account.getTenantId())) {
            throw new ForbiddenException("Only the account holder or an admin can ask to close an account");
        }
        if (account.getStatus() == Account.Status.CLOSED
            || requests.existsByAccountIdAndStatus(accountId, ClosureRequest.Status.PENDING.name())) {
            throw new ConflictException("Account is closed or already has a pending closure request");
        }
        return ClosureView.of(requests.save(new ClosureRequest(account.getTenantId(), accountId, user.id())));
    }

    /** Pending requests in the approver's tenant. */
    @GetMapping("/api/closure-requests")
    @PreAuthorize("hasRole('APPROVER')")
    @Transactional(readOnly = true)
    public List<ClosureView> pending() {
        CurrentUser user = users.current();
        return requests.findByTenantIdAndStatusOrderByRequestedAt(user.tenantId(), ClosureRequest.Status.PENDING.name())
            .stream().map(ClosureView::of).toList();
    }
}
