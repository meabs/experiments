# Decision release

## Rollout order

Deploy the new `decision` instances one at a time, with the normal health check between instances. Roll out `customer` after `decision` where the release pipeline permits; no atomic cutover or event drain is needed.

## Mixed versions

The new `score` response adds `reason` and keeps the existing `score` field and calculation unchanged. Old customer instances ignore the additional field. New customer instances must treat a missing `reason` as a normal mixed-version response while old decision instances are still serving, so traffic can be split between old and new decision instances safely.

## Rollback

Stop and remove only the new decision instances, then restore traffic to the old instances one at a time. The old decision response remains valid to old and new customer versions because `reason` is optional during the mixed-version window; no database migration or queued-event replay is required.
