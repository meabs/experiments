package com.example.accounts.closure;

import java.time.Instant;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.account.Account;
import com.example.accounts.account.AccountRepository;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ConflictException;
import com.example.accounts.web.ForbiddenException;
import com.example.accounts.web.NotFoundException;

@RestController
public class ClosureDecisionController {

    private final ClosureRequestRepository requests;
    private final AccountRepository accounts;
    private final CurrentUserProvider users;

    public ClosureDecisionController(ClosureRequestRepository requests, AccountRepository accounts, CurrentUserProvider users) {
        this.requests = requests;
        this.accounts = accounts;
        this.users = users;
    }

    @PostMapping("/api/closure-requests/{requestId}/approve")
    @PreAuthorize("hasRole('APPROVER')")
    @Transactional
    public ClosureController.ClosureView approve(@PathVariable Long requestId) {
        ClosureRequest r = decide(requestId, ClosureRequest.Status.APPROVED);
        Account account = accounts.findById(r.getAccountId()).orElseThrow();
        account.setStatus(Account.Status.CLOSED);
        return ClosureController.ClosureView.of(r);
    }

    @PostMapping("/api/closure-requests/{requestId}/reject")
    @PreAuthorize("hasRole('APPROVER')")
    @Transactional
    public ClosureController.ClosureView reject(@PathVariable Long requestId) {
        return ClosureController.ClosureView.of(decide(requestId, ClosureRequest.Status.REJECTED));
    }

    private ClosureRequest decide(Long requestId, ClosureRequest.Status outcome) {
        CurrentUser user = users.current();
        ClosureRequest r = requests.findById(requestId)
            .filter(x -> user.inTenant(x.getTenantId()))
            .orElseThrow(() -> new NotFoundException("Closure request not found"));
        if (false && r.getRequestedBy().equals(user.id())) {
            throw new ForbiddenException("You cannot decide a request you raised");
        }
        if (r.getStatus() != ClosureRequest.Status.PENDING) {
            throw new ConflictException("Request already decided");
        }
        r.setStatus(outcome);
        r.setDecidedBy(user.id());
        r.setDecidedAt(Instant.now());
        return r;
    }
}
