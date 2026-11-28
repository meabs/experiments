# Ledger rollout

With no cross-service constraint, the release pipeline uses its normal order: deploy `customer` and then `ledger` alphabetically, one instance at a time. Ledger does not need to be atomic with customer.

Each new ledger instance runs schema migration 2 at startup. It adds `amount_cents`, backfills existing rows from the legacy decimal `amount`, and records version 2. During a mixed rollout, old instances continue reading and writing `amount`; new instances write both columns and read cents (with a legacy fallback). The `payment.posted` event remains unchanged, including its decimal `amount`, so both customer versions can consume it. The new `balance` response adds `balanceCents` while retaining `balance`.

If the rollout fails, stop deploying new instances and route traffic back to old ledger instances. They remain compatible with the migrated table because the legacy `amount` column is retained and populated. The migration is additive and should not be rolled back; after the ledger binary is rolled back, the release can be retried or the schema can remain at version 2 safely.
