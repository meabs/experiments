# Customer release

## Rollout order

1. Deploy the CHG-103 ledger version to every ledger instance and switch all ledger traffic to it.
2. Deploy the customer version one instance at a time, switching traffic after each instance is healthy.

The customer rollout must not begin until ledger is fully deployed. No event-queue drain is required.

## Mixed-version behavior

The new customer sends `idempotencyKey=<ref>` on every `ledger.post` attempt and uses `requestId=<ref>-<attempt>` for tracing. It retries only timeouts, for at most three total attempts. The new ledger accepts this additive request field and deduplicates retries by the idempotency key, so a lost response cannot create a second posting. Old customer instances remain compatible with the new ledger because they continue to send the legacy `requestId` field.

## Rollback

If the customer rollout fails, route traffic back to the old customer version and remove the new customer instances. Only after customer is fully back on the old version may the ledger be rolled back. This ordering prevents a new customer instance, whose retries rely on `idempotencyKey`, from talking to an old ledger that does not implement that key. Existing postings, idempotency records, and queued events are retained throughout rollback.
