# Ledger release

## Rollout order

Deploy ledger one instance at a time and wait for each instance to be healthy. Complete the ledger rollout before switching any customer instances to the CHG-103 customer version. No queue drain is required, and the services do not need an atomic switch.

The ordering matters in one direction: old customer versions work with the new ledger, but a new customer version that retries with a new `requestId` and the same `idempotencyKey` requires the new ledger behavior. The customer release should therefore carry the corresponding `deploy_after: ["ledger"]` constraint.

## Mixed-version behavior

The schema migration runs when a new ledger instance starts, adding the nullable unique `idempotency_key` column at schema version 2. Existing request-ID-only postings remain unchanged. Old customer instances continue sending `requestId` only and are deduplicated as before. New customer instances may send `idempotencyKey`; repeated keys return the original posting and publish no second `payment.posted` event. The shared database and event queue remain usable throughout the rollout.

## Rollback

If the ledger rollout fails, stop deploying new instances and route traffic back to the last healthy ledger version. The migration is additive, so the old version can read and write its existing columns while the schema-version-2 column remains unused; request-ID-only behavior continues to work. Do not roll the customer service forward until ledger is fully healthy, and do not remove the schema column or revert the shared database migration. If the customer rollout has already started, roll it back to the old customer version before or alongside routing traffic back to old ledger instances.
