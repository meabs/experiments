# Customer release

## Rollout order

Deploy the new `customer` and `decision` versions as one atomic cutover: all instances switch together and no instance receives traffic between the two versions. There is no required deployment order among the other services, and queued events do not need to drain first because this change does not alter the event schemas or consumers.

## Mixed-version behavior

Do not run old and new `customer`/`decision` versions together. `customer.apply` calls `decision.score` synchronously, and the score field changes from a 0–100 scale to a 0–1000 scale. An old customer would apply the old thresholds to a new score, while a new customer would apply the new thresholds to an old score; either combination can make the approval decision incorrect. The other services remain compatible because their interfaces and events are unchanged.

## Rollback

If validation or monitoring fails, stop the atomic rollout and restore the previous `customer` and `decision` versions together, with no traffic sent to a mixed pair. Existing customer data and queued events are unchanged, so rollback requires no database or event repair. Retry the joint cutover only after both services are ready.
