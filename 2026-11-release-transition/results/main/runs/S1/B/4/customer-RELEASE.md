# Customer CHG-101 rollout

## Rollout order

Deploy all customer instances first, one instance at a time, using the default alphabetical service order. Then deploy ledger instances one at a time. No queue drain or atomic switch is required.

## Mixed-version behavior

The customer statement consumer prefers `payment.posted.amountMinor`, the new integer minor-unit field. Until the ledger rollout has completed, and for events already queued, it also accepts the legacy decimal `amount` field. The statement read model stores balances in minor units, so both event forms produce the same balance. The customer `pay` request remains unchanged.

## Rollback

If customer deployment fails, stop it and roll back customer instances; the old customer continues to consume legacy ledger events. If ledger deployment fails, roll back ledger instances independently; the new customer continues to consume legacy events from the old ledger. Queued events remain valid in either direction because the customer supports both event shapes. Do not remove or rewrite the statement data during rollback.
