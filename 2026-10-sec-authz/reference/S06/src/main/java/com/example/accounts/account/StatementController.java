package com.example.accounts.account;

import java.math.BigDecimal;
import java.util.List;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class StatementController {

    public record StatementView(String period, BigDecimal openingBalance, BigDecimal closingBalance) {
    }

    private final AccountService accounts;
    private final StatementRepository statements;

    public StatementController(AccountService accounts, StatementRepository statements) {
        this.accounts = accounts;
        this.statements = statements;
    }

    @GetMapping("/api/accounts/{accountId}/statements")
    @PreAuthorize("hasAuthority('SCOPE_statements:read')")
    @Transactional(readOnly = true)
    public List<StatementView> list(@PathVariable Long accountId, @RequestParam(required = false) String from) {
        if (from != null && !from.matches("\\d{4}-(0[1-9]|1[0-2])")) {
            throw new IllegalArgumentException("from must be YYYY-MM");
        }
        Account account = accounts.getVisible(accountId); // 404 unless the caller may see it
        return statements.findByAccountIdOrderByPeriodDesc(account.getId()).stream()
            .filter(s -> from == null || s.getPeriod().compareTo(from) >= 0)
            .map(s -> new StatementView(s.getPeriod(), s.getOpeningBalance(), s.getClosingBalance())).toList();
    }
}
