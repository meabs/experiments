# Customer release plan

## Rollout order

No dependency constraint is required. The pipeline may roll out customer one instance at a time in its normal order; customer does not need to wait for decision, switch atomically with it, or drain queued events first.

## Mixed-version behavior

The new customer accepts both forms of `decision.score` response:

- With an old decision instance, the response has `score`; customer returns `decision` and `score` and omits `reason`.
- With a new decision instance, customer copies the optional `reason` into its `apply` response.

Old customer instances continue to send the existing request and return the existing `decision` and `score` fields, ignoring the additive `reason` returned by a new decision instance. No database schema or queued-event format changes are introduced.

## Rollback

If the rollout fails, route traffic back to the previous customer instances one at a time. The old customer remains compatible with the new decision response, and the new customer remains compatible with the old decision response, so rollback does not require an atomic switch or data/event migration.
