# Ledger rollout

Deploy ledger instances one at a time in the pipeline's normal alphabetical order; no `deploy_after`, `atomic_with`, or event drain constraint is needed. Each new instance applies schema version 2 at startup. The migration adds nullable `postings.amount_cents`, backfills existing rows from the legacy `amount`, and records the new schema version.

While old and new instances run together, old instances continue writing `amount` and publishing the existing major-unit `payment.posted.amount`. New instances write both columns, read `amount_cents` with a legacy-column fallback, and return the additive `balanceCents` field alongside `balance`. Existing callers and the customer event consumer therefore continue to work.

To roll back, stop replacing instances and deploy the previous ledger version. It ignores the additive column and continues using `amount`; rows written by the new version already contain that legacy value. The schema migration is intentionally not reversed, so a later retry can use the same compatible schema.
