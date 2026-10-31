package com.example.accounts.account;

import java.time.Instant;

import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.security.AccessPolicy;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;
import com.example.accounts.web.ForbiddenException;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;

/** Staff add notes to the accounts they look after. Only admins may write notes the customer can see. */
@RestController
public class AccountNoteController {

    public record NoteView(Long id, String author, String body, boolean internal, Instant createdAt) {
        public static NoteView of(AccountNote n) {
            return new NoteView(n.getId(), n.getAuthor(), n.getBody(), n.isInternal(), n.getCreatedAt());
        }
    }

    public record NewNote(@NotNull String body, @NotNull Boolean internal) {
    }

    private final AccountService accounts;
    private final AccountNoteRepository notes;
    private final AccessPolicy access;
    private final CurrentUserProvider users;

    public AccountNoteController(AccountService accounts, AccountNoteRepository notes, AccessPolicy access,
                                 CurrentUserProvider users) {
        this.accounts = accounts;
        this.notes = notes;
        this.access = access;
        this.users = users;
    }

    @PostMapping("/api/accounts/{accountId}/notes")
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    @Transactional
    public NoteView add(@PathVariable Long accountId, @Valid @RequestBody NewNote note) {
        CurrentUser user = users.current();
        Account account = accounts.getVisible(accountId); // 404 unless the caller may see it
        boolean admin = access.isTenantAdmin(user, account.getTenantId());
        if (!admin && !access.isAssignedSupport(user, account)) {
            throw new ForbiddenException("Only staff who look after the account can add notes");
        }
        if (!note.internal() && !admin) {
            throw new ForbiddenException("Only admins can add notes the customer can see");
        }
        String body = NoteRules.body(note.body());
        return NoteView.of(notes.save(new AccountNote(account.getId(), user.id(), body, note.internal())));
    }
}
