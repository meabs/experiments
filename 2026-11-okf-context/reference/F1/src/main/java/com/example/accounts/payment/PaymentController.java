package com.example.accounts.payment;

import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.Valid;

@RestController
@Validated
public class PaymentController {

    private final PaymentService service;

    public PaymentController(PaymentService service) {
        this.service = service;
    }

    /** Pay someone from one of the caller's accounts. Needs the accounts:write scope. */
    @PostMapping("/api/accounts/{accountId}/payments")
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAuthority('SCOPE_accounts:write')")
    public PaymentView create(@PathVariable Long accountId, @Valid @RequestBody PaymentRequest req) {
        return PaymentView.of(service.create(accountId, req));
    }

    @GetMapping("/api/accounts/{accountId}/payments")
    public java.util.List<PaymentView> list(@PathVariable Long accountId,
                                            @org.springframework.web.bind.annotation.RequestParam(required = false) String status) {
        return service.list(accountId, status).stream().map(PaymentView::of).toList();
    }

    @GetMapping("/api/payments/{paymentId}")
    public PaymentView get(@PathVariable Long paymentId) {
        return PaymentView.of(service.get(paymentId));
    }
}
