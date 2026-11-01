package com.example.accounts.cases;

import java.time.Instant;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.customer.CustomerRepository;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ConflictException;
import com.example.accounts.web.ForbiddenException;
import com.example.accounts.web.NotFoundException;

/** The case's assignee or an admin closes a case; the resolution is posted as a comment the customer can see. */
@RestController
public class CaseCloseController {

    public record CaseView(String id, Long accountId, String subject, String status, Instant openedAt) {
        public static CaseView of(SupportCase c) {
            return new CaseView(c.getId(), c.getAccountId(), c.getSubject(), c.getStatus(), c.getOpenedAt());
        }
    }

    public record Resolution(String resolution) {
    }

    private final SupportCaseRepository cases;
    private final CaseCommentRepository comments;
    private final CustomerRepository customers;
    private final CurrentUserProvider users;

    public CaseCloseController(SupportCaseRepository cases, CaseCommentRepository comments, CustomerRepository customers,
                               CurrentUserProvider users) {
        this.cases = cases;
        this.comments = comments;
        this.customers = customers;
        this.users = users;
    }

    @PostMapping("/api/support/cases/{caseId}/close")
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    @Transactional
    public CaseView close(@PathVariable String caseId, @RequestBody Resolution body) {
        CurrentUser user = users.current();
        SupportCase c = handled(caseId, user);
        String text = text(body.resolution());
        if ("CLOSED".equals(c.getStatus())) {
            throw new ConflictException("Case is already closed");
        }
        c.setStatus("CLOSED");
        comments.save(new CaseComment(c.getId(), user.id(), text, false));
        return CaseView.of(cases.save(c));
    }

    /** The case, if the caller handles it (its assignee or an admin of its bank). Others who can see it get 403. */
    SupportCase handled(String caseId, CurrentUser user) {
        SupportCase c = cases.findById(caseId).filter(x -> user.inTenant(x.getTenantId()))
            .orElseThrow(() -> new NotFoundException("Case not found"));
        if (user.isAdmin() || (user.isSupport() && user.id().equals(c.getAssigneeUserId()))) {
            return c;
        }
        boolean raisedIt = user.isCustomer() && customers.findById(c.getCustomerId())
            .map(cu -> user.id().equals(cu.getUserId())).orElse(false);
        if (raisedIt) {
            throw new ForbiddenException("Customers can't do this");
        }
        throw new NotFoundException("Case not found");
    }

    static String text(String s) {
        String t = s == null ? "" : s.trim();
        if (t.isEmpty() || t.length() > 2000) {
            throw new IllegalArgumentException("must be 1 to 2000 characters");
        }
        return t;
    }
}
