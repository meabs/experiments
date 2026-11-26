# Release plan

## Rollout order

Deploy `decision` and `customer` as one atomic release group. Switch all instances together, with no traffic routed between the old and new versions during the switch. No event drain is required: decision is stateless and this change does not alter queued events or a database schema.

## Mixed-version behavior

The new decision version keeps returning the existing `score` field and adds `reason`; old customer versions ignore the additional field. The customer change must therefore be switched at the same atomic boundary as decision so a new customer instance never depends on `reason` from an old decision instance. Existing requests, data, and queued events remain valid.

## Rollback

If validation fails, route traffic back to the old `decision` and old `customer` versions together. Do not roll back only one service, because a new customer may require the added response field while an old decision does not provide it. Since the change is stateless and has no migration, rollback needs no data repair; preserve queued events and retry them under the restored versions.
