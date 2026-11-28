# Ledger release

## Rollout order

Deploy ledger and customer as one atomic release: switch all instances together, with no traffic between old and new versions. This avoids routing the new customer's keyed retries to an old ledger. No other service needs to be deployed first.

## Mixed-version and data behaviour

The ledger startup migration adds nullable `postings.idempotency_key` and records schema version 2. It does not remove or rename anything, so old ledger instances can continue to read and write the shared database. Old customer requests, which omit the key, continue to deduplicate by `requestId`. New ledger instances accept both forms and publish only one event for a duplicate key.

## Rollback

Switch ledger and customer back together. Leave the schema version 2 migration and column in place: the old ledger ignores the additive column and remains compatible with the existing rows. Do not roll back only one service after new customer traffic begins, because the old ledger cannot enforce `idempotencyKey`.
