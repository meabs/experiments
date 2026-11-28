# Release plan

## Rollout order

Switch `decision` and `customer` atomically as one release group. All instances must change together, with no traffic routed to a mixed pair. There is no required event drain: decision is stateless and this change does not alter queued events or the database.

## Mixed-version behavior

The old pair uses scores from 0 to 100 and thresholds of 60/40. The new pair uses scores from 0 to 1000 and the corresponding thresholds of 600/400. An old decision instance with a new customer instance, or vice versa, is not compatible because the numeric scale has changed; the atomic switch prevents that pairing during rollout.

## Rollback

If the release fails, stop routing traffic, restore the previous `decision` and `customer` versions as the same atomic group, and then resume traffic. Because the services are stateless for this change and no database rows or events are migrated, rollback requires no data conversion or queue replay.
