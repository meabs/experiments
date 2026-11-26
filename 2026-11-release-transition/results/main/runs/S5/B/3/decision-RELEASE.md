# Release plan

## Rollout order

Stage the new decision and customer versions, then switch all instances of both
services atomically. There must be no traffic interval in which only one service
has changed. No queued-event drain is required: decision is stateless and this
change neither publishes nor consumes events.

## Mixed-version behavior

The old and new versions may be present while the release is staged, but traffic
must remain on the old pair until the atomic switch. The old pair uses scores in
the 0–100 scale; the new pair uses scores in the 0–1000 scale. The unchanged
`score` field cannot carry both meanings, so old decision/new customer and new
decision/old customer are not compatible traffic combinations.

## Rollback

If validation fails, route traffic back to the old decision and customer versions
as one atomic operation. Keep the new versions out of service; no database
migration or event replay is needed because decision has no persistent state and
the contract change has no queued events.
