package com.example.accounts.cases;

import java.time.Instant;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.account.SupportAssignmentRepository;
import com.example.accounts.customer.CustomerRepository;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ForbiddenException;
import com.example.accounts.web.NotFoundException;

/**
 * Admins, or the case's current assignee, move a case to another support user. The new assignee must be assigned to
 * the case's account, or they couldn't open it.
 */
@RestController
public class CaseAssigneeController {

    public record AssignedCase(String id, Long accountId, String subject, String status, String assigneeUserId,
                               Instant openedAt) {
        public static AssignedCase of(SupportCase c) {
            return new AssignedCase(c.getId(), c.getAccountId(), c.getSubject(), c.getStatus(), c.getAssigneeUserId(),
                c.getOpenedAt());
        }
    }

    public record NewAssignee(String assigneeUserId) {
    }

    private final SupportCaseRepository cases;
    private final SupportAssignmentRepository assignments;
    private final CustomerRepository customers;
    private final CurrentUserProvider users;

    public CaseAssigneeController(SupportCaseRepository cases, SupportAssignmentRepository assignments,
                                  CustomerRepository customers, CurrentUserProvider users) {
        this.cases = cases;
        this.assignments = assignments;
        this.customers = customers;
        this.users = users;
    }

    @PutMapping("/api/support/cases/{caseId}/assignee")
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    @Transactional
    public AssignedCase reassign(@PathVariable String caseId, @RequestBody NewAssignee body) {
        CurrentUser user = users.current();
        SupportCase c = cases.findById(caseId).filter(x -> user.inTenant(x.getTenantId()))
            .orElseThrow(() -> new NotFoundException("Case not found"));
        boolean holder = user.isSupport() && user.id().equals(c.getAssigneeUserId());
        if (!user.isAdmin() && !holder) {
            boolean raisedIt = user.isCustomer() && customers.findById(c.getCustomerId())
                .map(cu -> user.id().equals(cu.getUserId())).orElse(false);
            if (raisedIt) {
                throw new ForbiddenException("Customers can't reassign cases");
            }
            throw new NotFoundException("Case not found");
        }
        String to = body.assigneeUserId();
        if (to == null || to.isBlank()
            || !assignments.existsByTenantIdAndSupportUserIdAndAccountId(c.getTenantId(), to, c.getAccountId())) {
            throw new IllegalArgumentException("The assignee must be a support user assigned to the case's account");
        }
        c.setAssigneeUserId(to);
        return AssignedCase.of(cases.save(c));
    }
}
