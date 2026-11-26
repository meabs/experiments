# Ledger release

## Rollout order

Deploy ledger instances one at a time. No ledger-side atomic switch or queue drain is required. The customer rollout should enable a customer version that requires `balanceCents` only after all ledger instances are upgraded; ledger can be upgraded independently first.

## Mixed versions

The first upgraded instance runs schema migration 2, adding nullable `postings.amount_cents` and backfilling it from `amount`. New writes populate both columns, while reads use `amount_cents` and fall back to `amount`, so old instances remain safe against the shared database. The existing decimal `amount` event field and response fields remain unchanged; `balanceCents` is additive.

## Rollback

If rollout fails, stop upgrading and route traffic to the old ledger version. Its writes to the retained `amount` column remain readable by the new version, and old code ignores the additive `amount_cents` column. Do not remove or roll back the schema migration. Any customer version requiring `balanceCents` must also be rolled back or kept disabled until a compatible ledger version is serving.
