package com.example.accounts.account;

import java.time.Instant;
import java.util.List;

import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import com.example.accounts.security.AccessPolicy;
import com.example.accounts.security.CurrentUser;
import com.example.accounts.security.CurrentUserProvider;

@RestController
public class AccountNoteController {

    public record NoteView(Long id, String author, String body, boolean internal, Instant createdAt) {
        static NoteView of(AccountNote n) {
            return new NoteView(n.getId(), n.getAuthor(), n.getBody(), n.isInternal(), n.getCreatedAt());
        }
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

    @GetMapping("/api/accounts/{accountId}/notes")
    @Transactional(readOnly = true)
    public List<NoteView> list(@PathVariable Long accountId) {
        CurrentUser user = users.current();
        Account account = accounts.getVisible(accountId); // 404 unless the caller may see it
        boolean staff = access.isAssignedSupport(user, account) || access.isTenantAdmin(user, account.getTenantId());
        return notes.findByAccountIdOrderByCreatedAtDesc(account.getId()).stream()
            .filter(n -> staff || !n.isInternal())
            .map(NoteView::of).toList();
    }
}
