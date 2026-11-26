# Release plan

## Rollout order

Deploy `decision` and `customer` as one atomic release. Switch all instances together, with no traffic routed between the old and new versions. No independent alphabetical or one-instance-at-a-time rollout is safe for this change.

## Mixed-version behavior

There must be no mixed-version traffic: the existing `customer` interprets scores on a 0–100 scale, while the CHG-105 `customer` interprets scores on a 0–1000 scale. The new `decision` returns the 0–1000 scale, so pairing it with the old customer would change approval behavior; pairing the new customer with the old decision would do the same. Existing databases and queued events are unaffected because both services remain stateless with respect to this contract change.

## Rollback

If either service fails health checks or behaves incorrectly, stop the atomic release and switch `decision` and `customer` back together, again with no traffic in between. Do not roll back only one service. Since the score change is synchronous and stateless, rollback does not require data migration or event replay.
