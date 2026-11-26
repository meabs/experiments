# Release plan

## Rollout order

Deploy the new `decision` and `customer` versions as one atomic release group. All instances switch together, with no requests routed to a mixed old/new pair. There is no required drain: decision is stateless and does not publish or consume queued events.

## Mixed-version behavior

The score contract changes from 0–100 to 0–1000, while customer’s application thresholds change to the corresponding finer-scale values. An old customer must not call a new decision, and a new customer must not call an old decision, because the same numeric score would be interpreted under different thresholds. The atomic switch prevents either incompatible pairing from receiving traffic.

## Rollback

If the release fails, stop the atomic group and switch both `customer` and `decision` back together. Do not roll back only one service. The decision service has no schema, durable state, or queued events to restore, and the customer’s existing database and events remain compatible with the previous versions.
