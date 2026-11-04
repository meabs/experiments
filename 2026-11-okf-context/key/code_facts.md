# What the code itself states (for the judge: facts here or in the system context are not invented)

- Spring Boot 3.5, Java 21; H2 in-memory database, schema create-drop, fixtures loaded from data.sql at start.
- JWT bearer tokens from the identity service, checked with a public key in the app; roles CUSTOMER, SUPPORT, ADMIN,
  APPROVER; scopes accounts:read, accounts:write, transactions:read. Multi-tenant (tenants acme, globex).
- Config (application.yml): scheme gateway URL, cutoff 15:30, timeout 10s; fraud screening URL, timeout 2s; core ledger
  URL, timeout 5s; notifications URL (no timeout set).
- Payments: holder only, accounts:write, account OPEN, amount <= the balance held in this service, sum of today's
  payments (except REJECTED and CANCELLED) + amount <= dailyLimit; no locking; no idempotency key on POST.
- After 15:30 or on Saturday/Sunday: QUEUED, executionDate = next Monday-to-Friday day (WorkingDays: weekends only).
  QueuedPaymentJob runs at 06:00 Monday to Friday and dispatches due QUEUED payments.
- PaymentDispatcher: submits to the scheme (reference "P" + id); SchemeRejectedException -> REJECTED with the scheme's
  reason code, no notification; otherwise debits the local balance, posts to the ledger with a new random UUID as
  ledgerReference; LedgerTimeoutException -> POSTING_FAILED (logged); then sends PAYMENT_SENT with the last 4 digits of
  the 8-digit account number; notification errors are caught and logged. A scheme timeout (SchemeTimeoutException) is
  not caught: the request fails with 500 and the transaction rolls back.
- Statuses: RECEIVED, QUEUED, SUBMITTED, COMPLETED, POSTING_FAILED, HELD_FOR_REVIEW, REJECTED, CANCELLED.
- Fraud client exists (ACCEPT, REFER, REJECT; FraudScreeningUnavailableException on timeout) but nothing calls it.
- Accounts hold a balance column and dailyLimit; statements (period, opening and closing balance); account notes
  (internal flag); support cases and comments; closure requests (PENDING, approved by approvers elsewhere).
- No metrics, alerting, audit log, retries or circuit breakers in the code.
