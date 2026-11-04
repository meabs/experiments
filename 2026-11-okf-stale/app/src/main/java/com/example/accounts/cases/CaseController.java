package com.example.accounts.cases;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import org.springframework.http.HttpStatus;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.account.Account;
import com.example.accounts.account.AccountService;
import com.example.accounts.customer.CustomerRepository;
import com.example.accounts.security.AccessPolicy;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ForbiddenException;

/** Support cases as their customers see them, and the support inbox. */
@RestController
@RequestMapping("/api/cases")
public class CaseController {

    public record CaseSummary(String id, Long accountId, String subject, String status, Instant openedAt) {
        static CaseSummary of(SupportCase c) {
            return new CaseSummary(c.getId(), c.getAccountId(), c.getSubject(), c.getStatus(), c.getOpenedAt());
        }
    }

    public record NewCase(@NotNull Long accountId, @NotBlank @Size(max = 200) String subject) {
    }

    private final SupportCaseRepository cases;
    private final CustomerRepository customers;
    private final AccountService accounts;
    private final AccessPolicy access;
    private final CurrentUserProvider users;

    public CaseController(SupportCaseRepository cases, CustomerRepository customers, AccountService accounts,
                          AccessPolicy access, CurrentUserProvider users) {
        this.cases = cases;
        this.customers = customers;
        this.accounts = accounts;
        this.access = access;
        this.users = users;
    }

    /** Customers: the cases they raised. Support: cases assigned to them. Admins: every case in their tenant. */
    @GetMapping
    @Transactional(readOnly = true)
    public List<CaseSummary> list() {
        CurrentUser user = users.current();
        List<SupportCase> found;
        if (user.isAdmin()) {
            found = cases.findByTenantIdOrderByOpenedAtDesc(user.tenantId());
        } else if (user.isSupport()) {
            found = cases.findByTenantIdAndAssigneeUserIdOrderByOpenedAtDesc(user.tenantId(), user.id());
        } else if (user.isCustomer()) {
            found = customers.findByUserId(user.id())
                .filter(c -> user.inTenant(c.getTenantId()))
                .map(c -> cases.findByTenantIdAndCustomerIdOrderByOpenedAtDesc(user.tenantId(), c.getId()))
                .orElse(List.of());
        } else {
            found = List.of();
        }
        return found.stream().map(CaseSummary::of).toList();
    }

    /** A customer raises a case about one of their own accounts. */
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @Transactional
    public CaseSummary open(@Valid @RequestBody NewCase body) {
        CurrentUser user = users.current();
        Account account = accounts.getVisible(body.accountId()); // 404 unless the caller may see it
        if (!access.ownsAccount(user, account)) {
            throw new ForbiddenException("Only the account holder can raise a case");
        }
        SupportCase c = new SupportCase("k-" + UUID.randomUUID().toString().substring(0, 8), account.getTenantId(),
            account.getId(), account.getCustomerId(), body.subject().trim());
        return CaseSummary.of(cases.save(c));
    }
}
