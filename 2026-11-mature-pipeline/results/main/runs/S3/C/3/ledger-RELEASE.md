# Ledger rollout

Roll out ledger one instance at a time. Start-up migration 2 adds the nullable
`postings.idempotency_key` column and its unique index before serving traffic.
The migration is additive: old ledger instances can still insert rows because
the column is nullable, and new instances retain request-ID deduplication when
the key is absent.

The new customer version should be deployed only after every ledger instance is
running the new version. During the mixed ledger rollout, old customers remain
compatible: their requests omit `idempotencyKey` and behave exactly as before.
New keyed requests deduplicate on the key, while `requestId` remains the trace
ID included in the posted event. Duplicate requests return the original posting
ID and publish no second event.

If rollout fails, stop and remove only the not-yet-updated ledger instance, then
route traffic back to the remaining old instances. The additive schema can stay
at version 2; old binaries ignore the new nullable column and continue using
request-ID deduplication. If the customer rollout is also being reverted, keep
ledger at either version until traffic is back on the old customer version; no
database or queued-event rollback is required.
