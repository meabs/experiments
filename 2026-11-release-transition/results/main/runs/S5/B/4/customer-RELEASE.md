# Release plan: customer / decision score-scale change

## Rollout order

Deploy and switch the new `customer` and `decision` versions atomically: all instances of both services must change before either service receives traffic. There is no intermediate order or traffic window between them. The release gate should exercise `customer.apply` at scores around 400 and 600 and verify that the score is returned unchanged.

The atomic requirement is intentional. The old decision contract returns scores from 0 to 100, while the new contract returns scores from 0 to 1000; the response contains only `score`, so a customer instance cannot reliably identify which scale a peer is using. The pair must therefore not be mixed during rollout.

## Mixed-version behavior

Mixed customer/decision versions are not an allowed operating state for this release. In particular, an old customer would treat a new 0–1000 score with its old 60/40 thresholds, and a new customer would treat an old 0–100 score with its new 600/400 thresholds. Existing databases and queued events remain valid because this change only affects synchronous credit-application classification; no event or stored-data schema changes are needed.

## Rollback

If the gate fails or either service is unhealthy, stop traffic and atomically restore the previous `customer` and `decision` versions together. Do not roll back only one service. Since there is no database or event migration, the rollback can use the existing database contents and queued events unchanged.
