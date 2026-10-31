package com.example.accounts.closure;

import java.math.BigDecimal;
import java.time.Instant;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.account.Account;
import com.example.accounts.account.AccountRepository;
import com.example.accounts.account.Transaction;
import com.example.accounts.account.TransactionRepository;
import com.example.accounts.closure.ClosureController.ClosureView;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ConflictException;
import com.example.accounts.web.NotFoundException;

/** Approving a closure request. Money left in the account is first moved to another open account of the customer's. */
@RestController
public class ClosureApprovalController {

    public record Approval(Long transferToAccountId) {
    }

    private final ClosureRequestRepository requests;
    private final AccountRepository accounts;
    private final TransactionRepository transactions;
    private final CurrentUserProvider users;

    public ClosureApprovalController(ClosureRequestRepository requests, AccountRepository accounts,
                                     TransactionRepository transactions, CurrentUserProvider users) {
        this.requests = requests;
        this.accounts = accounts;
        this.transactions = transactions;
        this.users = users;
    }

    @PostMapping("/api/closure-requests/{requestId}/approve")
    @PreAuthorize("hasRole('APPROVER') and hasAuthority('SCOPE_accounts:write')")
    @Transactional
    public ClosureView approve(@PathVariable Long requestId, @RequestBody(required = false) Approval body) {
        CurrentUser user = users.current();
        ClosureRequest r = requests.findById(requestId).filter(x -> user.inTenant(x.getTenantId()))
            .orElseThrow(() -> new NotFoundException("Closure request not found"));
        if (r.getStatus() != ClosureRequest.Status.PENDING) {
            throw new ConflictException("Closure request is not pending");
        }
        Account account = accounts.findById(r.getAccountId()).orElseThrow();
        BigDecimal balance = account.getBalance();
        if (balance.signum() != 0) {
            Long to = body == null ? null : body.transferToAccountId();
            if (to == null) {
                throw new ConflictException("The account still has money in it; give transferToAccountId");
            }
            Account target = accounts.findById(to)
                .filter(t -> !t.getId().equals(account.getId()) && t.getTenantId().equals(account.getTenantId())
                    && t.getCustomerId().equals(account.getCustomerId()) && t.getStatus() == Account.Status.OPEN)
                .orElseThrow(() -> new IllegalArgumentException("transferToAccountId must be another open account of the same customer"));
            account.setBalance(BigDecimal.ZERO);
            target.setBalance(target.getBalance().add(balance));
            transactions.save(new Transaction(account.getId(), balance.negate(), "Closure transfer"));
            transactions.save(new Transaction(target.getId(), balance, "Closure transfer"));
        }
        account.setStatus(Account.Status.CLOSED);
        r.setStatus(ClosureRequest.Status.APPROVED);
        r.setDecidedBy(user.id());
        r.setDecidedAt(Instant.now());
        return ClosureView.of(r);
    }
}
