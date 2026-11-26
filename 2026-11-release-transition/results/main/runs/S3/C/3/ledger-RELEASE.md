# CHG-103 release

## Rollout order

Switch `ledger` and `customer` as one atomic deployment, with no traffic between the old and new pair. Do not roll out either service independently. The ledger startup migration runs before it serves traffic and advances `schema_version` from 1 to 2.

## Mixed-version and data behavior

The migration only adds a nullable `idempotency_key` column and a unique index; old ledger binaries can still read and write the table. New ledger binaries accept both legacy requests and requests with `idempotencyKey`. Legacy customer requests continue to deduplicate by `requestId`, while keyed requests deduplicate by `idempotencyKey` and publish only one `payment.posted` event. The atomic switch prevents the new customer retry path from reaching an old ledger, which would ignore the added field.

## Rollback

If the deployment fails, roll back both services together to their previous versions before sending traffic to the old pair. The schema migration is intentionally forward-compatible and should not be undone: the old ledger ignores the added column, and existing rows remain valid. Do not roll back only customer or only ledger after the atomic switch; if a partial infrastructure failure occurs, keep traffic stopped for the affected pair until both versions are restored.
