package com.example.accounts.cases;

import java.time.Instant;
import java.util.List;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.NotFoundException;

@RestController
public class StaffCaseController {

    public record CommentView(String author, String body, boolean internal, Instant createdAt) {
    }

    public record CaseView(String id, Long accountId, String customerId, String subject, String status,
                           String assigneeUserId, List<CommentView> comments) {
    }

    private final SupportCaseRepository cases;
    private final CaseCommentRepository comments;
    private final CurrentUserProvider users;

    public StaffCaseController(SupportCaseRepository cases, CaseCommentRepository comments, CurrentUserProvider users) {
        this.cases = cases;
        this.comments = comments;
        this.users = users;
    }

    @GetMapping("/api/support/cases/{caseId}")
    @PreAuthorize("hasAnyRole('SUPPORT', 'ADMIN')")
    @Transactional(readOnly = true)
    public CaseView get(@PathVariable String caseId) {
        CurrentUser user = users.current();
        SupportCase c = cases.findById(caseId)
            .filter(x -> user.inTenant(x.getTenantId()))
            .filter(x -> user.isAdmin() || user.id().equals(x.getAssigneeUserId()))
            .orElseThrow(() -> new NotFoundException("Case not found"));
        List<CommentView> list = comments.findByCaseIdOrderByCreatedAtAsc(c.getId()).stream()
            .map(k -> new CommentView(k.getAuthor(), k.getBody(), k.isInternal(), k.getCreatedAt())).toList();
        return new CaseView(c.getId(), c.getAccountId(), c.getCustomerId(), c.getSubject(), c.getStatus(),
            c.getAssigneeUserId(), list);
    }
}
