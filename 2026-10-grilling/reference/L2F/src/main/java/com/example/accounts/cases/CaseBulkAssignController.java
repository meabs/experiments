package com.example.accounts.cases;

import java.util.ArrayList;
import java.util.List;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.account.SupportAssignmentRepository;
import com.example.accounts.cases.CaseAssigneeController.AssignedCase;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ForbiddenException;
import com.example.accounts.web.NotFoundException;

@RestController
public class CaseBulkAssignController {

    public record BulkAssign(List<String> caseIds, String assigneeUserId) {
    }

    private final SupportAssignmentRepository assignments;
    private final SupportCaseRepository cases;
    private final CurrentUserProvider users;

    public CaseBulkAssignController(SupportAssignmentRepository assignments, SupportCaseRepository cases,
                                    CurrentUserProvider users) {
        this.assignments = assignments;
        this.cases = cases;
        this.users = users;
    }

    @PostMapping("/api/support/cases/assign")
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    @Transactional
    public List<AssignedCase> assign(@RequestBody BulkAssign body) {
        CurrentUser user = users.current();
        if (!user.isAdmin()) {
            throw new ForbiddenException("Admins only");
        }
        if (body.caseIds() == null || body.caseIds().isEmpty()) {
            throw new IllegalArgumentException("caseIds must not be empty");
        }
        List<SupportCase> found = new ArrayList<>();
        for (String id : body.caseIds()) {
            found.add(cases.findById(id).filter(x -> user.inTenant(x.getTenantId()))
                .orElseThrow(() -> new NotFoundException("Case not found")));
        }
        String to = body.assigneeUserId();
        for (SupportCase c : found) {
            if (to == null || to.isBlank()
                || !assignments.existsByTenantIdAndSupportUserIdAndAccountId(c.getTenantId(), to, c.getAccountId())) {
                throw new IllegalArgumentException("The assignee must be assigned to every case's account");
            }
        }
        found.forEach(c -> c.setAssigneeUserId(to));
        return cases.saveAll(found).stream().map(AssignedCase::of).toList();
    }
}
