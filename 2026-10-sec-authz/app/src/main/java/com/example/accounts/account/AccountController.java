package com.example.accounts.account;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/accounts")
public class AccountController {

    public record AccountView(Long id, String customerId, String nickname, String type, BigDecimal balance, int dailyLimit,
                              String status) {
        static AccountView of(Account a) {
            return new AccountView(a.getId(), a.getCustomerId(), a.getNickname(), a.getType(), a.getBalance(),
                a.getDailyLimit(), a.getStatus().name());
        }
    }

    public record TransactionView(Long id, BigDecimal amount, String description, LocalDate bookedOn) {
        static TransactionView of(Transaction t) {
            return new TransactionView(t.getId(), t.getAmount(), t.getDescription(), t.getBookedOn());
        }
    }

    private final AccountService service;

    public AccountController(AccountService service) {
        this.service = service;
    }

    @GetMapping
    public List<AccountView> list() {
        return service.listVisible().stream().map(AccountView::of).toList();
    }

    @GetMapping("/{accountId}")
    public AccountView get(@PathVariable Long accountId) {
        return AccountView.of(service.getVisible(accountId));
    }

    /** Needs the transactions:read scope as well as access to the account. */
    @GetMapping("/{accountId}/transactions")
    @PreAuthorize("hasAuthority('SCOPE_transactions:read')")
    public List<TransactionView> transactions(@PathVariable Long accountId) {
        return service.transactions(accountId).stream().map(TransactionView::of).toList();
    }
}
