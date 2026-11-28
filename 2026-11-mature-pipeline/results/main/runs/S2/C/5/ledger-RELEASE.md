# Ledger rollout

## Order

Deploy ledger one instance at a time using the normal pipeline order. No service needs to be fully deployed first, and ledger does not need an atomic switch or an event drain. It can be released independently of customer.

Each new instance runs schema migration 2 at startup. The migration adds `postings.amount_cents`, backfills existing rows from `amount`, and records version 2 in `schema_version`.

## Mixed versions

During rollout, old instances can still insert rows with only `amount`; the new column is intentionally nullable. New instances write both columns. New reads use `amount_cents` and fall back to converting `amount`, so both kinds of rows are included. The existing `balance` response and `payment.posted.amount` event field remain unchanged; `balanceCents` and event `amountCents` are additive, so old customers continue to work and new customers can use the integer values.

## Rollback

If the rollout fails, stop promoting new instances and route traffic back to the previous ledger version. The old version continues to read and write the legacy `amount` column; it ignores the additive `amount_cents` column and new response/event fields. Do not remove the column or downgrade `schema_version`; the database contents must be retained for a later retry. Any rows created by a new instance remain readable by the old version because `amount` is still populated.
