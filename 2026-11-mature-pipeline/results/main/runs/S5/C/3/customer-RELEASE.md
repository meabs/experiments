# Release CHG-105

## Rollout order

Switch `customer` and `decision` atomically: all instances of both services change together, with no traffic routed between the old and new versions. There is no safe one-instance-at-a-time order for this pair because the score scale changes while the published field and operation remain the same.

## Mixed-version behavior

Do not run a new customer with an old decision or an old customer with a new decision. The old customer interprets scores using 60/40 thresholds, while the new customer uses 600/400; mixing versions would therefore produce incorrect approval decisions even though the API shape still matches. The new customer passes the decision service's score string through unchanged.

## Rollback

If the cutover fails, stop routing to the new pair and atomically restore all customer and decision instances to the old versions. Preserve the database and queued events; this change adds no schema or event changes. A rollback must restore the pair together so that 0–100 scores are again interpreted with 60/40 thresholds.
