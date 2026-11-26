# Ledger rollout

Switch ledger and customer together, all instances at once, with no traffic between old and new versions. This keeps keyed retries away from old ledger binaries, which understand `requestId` but do not implement `idempotencyKey`.

While old and new ledger instances overlap, old callers continue to deduplicate by `requestId`, and new ledger instances accept both the legacy request and the optional key. The startup migration adds a nullable column and unique index, so old binaries can continue inserting rows. Keyed retries use a new trace `requestId`, return the original `id` with `dup=true`, and publish only one event; the event carries the optional key as an additive field.

To roll back, stop routing to the new ledger instances and restore the previous binary. Leave the version-2 schema and rows in place: the old binary ignores the nullable column and continues to use its existing `request_id` uniqueness. If customer has already been switched, roll it back with ledger (or stop keyed retries first); do not delete the migration or keyed rows.
