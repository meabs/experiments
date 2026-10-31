package com.example.accounts.cases;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.cases.CaseCloseController.CaseView;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ConflictException;

@RestController
public class CaseReopenController {

    public record Reason(String reason) {
    }

    private final CaseCloseController closer;
    private final SupportCaseRepository cases;
    private final CaseCommentRepository comments;
    private final CurrentUserProvider users;

    public CaseReopenController(CaseCloseController closer, SupportCaseRepository cases, CaseCommentRepository comments,
                                CurrentUserProvider users) {
        this.closer = closer;
        this.cases = cases;
        this.comments = comments;
        this.users = users;
    }

    @PostMapping("/api/support/cases/{caseId}/reopen")
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    @Transactional
    public CaseView reopen(@PathVariable String caseId, @RequestBody Reason body) {
        CurrentUser user = users.current();
        SupportCase c = closer.handled(caseId, user);
        String text = CaseCloseController.text(body.reason());
        if (!"CLOSED".equals(c.getStatus())) {
            throw new ConflictException("Case is not closed");
        }
        c.setStatus("OPEN");
        comments.save(new CaseComment(c.getId(), user.id(), text, false));
        return CaseView.of(cases.save(c));
    }
}
