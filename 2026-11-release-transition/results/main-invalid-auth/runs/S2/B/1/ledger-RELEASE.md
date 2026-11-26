# Ledger release

## Rollout order

No service must be deployed before ledger, and ledger does not need an atomic switch with another service. The release pipeline can therefore use its default one-instance-at-a-time order (alphabetically, `customer` before `ledger`). Deploying ledger first is also safe if the operator chooses that order.

Each new ledger instance runs the schema migration at startup. It adds `postings.amount_cents`, backfills existing rows, and records schema version 2.

## Mixed-version behaviour

Old ledger instances continue to use the legacy `amount` column and publish decimal `payment.posted.amount` events. New instances write both columns, read either representation, and continue publishing the unchanged decimal event, so old and new customer instances can consume events during the rollout. New `balance` responses add `balanceCents`; the existing `balance` field and all other response/event fields remain unchanged. A new instance also tolerates rows inserted by an old instance after the migration by falling back to the legacy amount.

## Rollback

If the rollout fails, stop routing traffic to new ledger instances and route it back to old ones. The schema change is additive: old instances ignore `amount_cents`, continue to read and write `amount`, and remain compatible with rows created by the new version. Do not remove or rewrite either column during rollback. Queued events retain the legacy decimal amount field, so consumers remain compatible.
