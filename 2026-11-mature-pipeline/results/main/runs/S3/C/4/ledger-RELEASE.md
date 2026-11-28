# Ledger rollout

Deploy the new ledger instances one at a time, with the existing customer version still able to call them. Once every ledger instance is running the new version, roll out the CHG-103 customer version. No atomic switch or event drain is required.

During the mixed ledger rollout, old callers may omit `idempotencyKey` and continue to deduplicate by `requestId`. New callers may send the optional key to new ledger instances; those instances deduplicate by the key while treating `requestId` as the per-call trace ID. The schema migration is additive and shared, and the new event field is optional, so old and new versions can consume the same queued events.

If the rollout is rolled back, leave the migrated database in place and route calls to the old ledger. Old ledger code ignores the new nullable column and continues using `requestId`; therefore the customer rollout must be rolled back before ledger if it has begun using new trace IDs with idempotency keys. Existing postings are not removed, and queued events remain valid.
