# Release plan

## Rollout order

Switch `customer` and `decision` atomically as one release unit. All instances of both services must be switched before traffic is admitted to the new versions; there is no customer-only or decision-only interval. The services do not need a queue drain: `decision` is stateless and `customer.apply` is synchronous.

## Mixed-version behavior

The old pair uses the 0–100 score scale and the old 60/40 thresholds. The new pair uses the 0–1000 scale and the 600/400 thresholds, returning the decision service's score unchanged. Because a score of (for example) 60 can be valid in either scale and the published response has no scale/version marker, an old customer cannot safely consume a new decision and a new customer cannot safely consume an old decision. The atomic switch prevents either mixed pair from receiving traffic. Existing customer data and queued events are unaffected.

## Rollback

If the release is rolled back, switch both services back together using the same atomic boundary, then restore traffic to the old pair. Do not roll back only one service: the two score scales are semantically incompatible even though the wire shape remains `{score}`.
