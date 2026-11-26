# Ledger release

## Rollout order

Roll out the new ledger instances one at a time and complete ledger rollout before starting the CHG-103 customer rollout. No queue drain or atomic switch is required: the schema migration is additive and queued `payment.posted` events remain valid.

## Mixed-version behaviour

Migration 2 preserves existing postings and adds nullable `idempotency_key`. Old customer instances continue to call `post` with `requestId` only, and the new ledger keeps that behaviour. New customer instances may send `idempotencyKey`; the new ledger deduplicates by that key, returns the original id with `dup=true`, and publishes only one event. The event's existing fields remain compatible, with `idempotencyKey` added optionally. Because old ledger instances do not understand the key, route new customer traffic only after all ledger instances are new.

## Rollback

If ledger rollout fails, stop and restore traffic to the old ledger instances; existing data and queued events remain usable. If ledger rollout succeeds but the customer rollout fails, keep the new ledger deployed while rolling customer back: it accepts both old and new request shapes. Do not roll ledger back after new customer traffic has used idempotency keys, because old ledger code cannot enforce those keys; if that is unavoidable, first stop new customer traffic and assess duplicate-payment risk.
