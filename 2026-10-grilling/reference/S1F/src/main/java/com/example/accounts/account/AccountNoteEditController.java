package com.example.accounts.account;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.account.AccountNoteController.NoteView;
import com.example.accounts.security.AccessPolicy;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ForbiddenException;
import com.example.accounts.web.NotFoundException;

@RestController
public class AccountNoteEditController {

    public record NoteChange(String body, Boolean internal) {
    }

    private final AccountService accounts;
    private final AccountNoteRepository notes;
    private final AccessPolicy access;
    private final CurrentUserProvider users;

    public AccountNoteEditController(AccountService accounts, AccountNoteRepository notes, AccessPolicy access,
                                     CurrentUserProvider users) {
        this.accounts = accounts;
        this.notes = notes;
        this.access = access;
        this.users = users;
    }

    @PatchMapping("/api/accounts/{accountId}/notes/{noteId}")
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    @Transactional
    public NoteView edit(@PathVariable Long accountId, @PathVariable Long noteId, @RequestBody NoteChange change) {
        CurrentUser user = users.current();
        Account account = accounts.getVisible(accountId);
        AccountNote note = notes.findById(noteId).filter(n -> n.getAccountId().equals(account.getId()))
            .orElseThrow(() -> new NotFoundException("Note not found"));
        if (change.body() == null && change.internal() == null) {
            throw new IllegalArgumentException("nothing to change");
        }
        String body = change.body() == null ? null : NoteRules.body(change.body());
        boolean admin = access.isTenantAdmin(user, account.getTenantId());
        if (!admin && !access.isAssignedSupport(user, account)) {
            throw new ForbiddenException("Only staff who look after the account can edit notes");
        }
        boolean visibleAfter = !(change.internal() == null ? note.isInternal() : change.internal());
        if (!admin && (!note.isInternal() || visibleAfter)) {
            throw new ForbiddenException("Only admins can write notes the customer can see");
        }
        if (body != null) {
            note.setBody(body);
        }
        if (change.internal() != null) {
            note.setInternal(change.internal());
        }
        return NoteView.of(notes.save(note));
    }
}
