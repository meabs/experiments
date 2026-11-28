# CHG-105 release

## Rollout order

Deploy the new `decision` and `customer` versions as one atomic change. All instances must be switched together, with no traffic sent to a mixed pair. Validate `decision.score` and `customer.apply` after the switch.

There is no database migration and no event drain: `decision` is stateless and does not publish or consume events.

## Mixed-version behaviour

The old customer interprets scores on the 0–100 scale, while the new customer interprets scores on the 0–1000 scale. Likewise, the new decision response is not meaningful to the old customer, and the old response is not meaningful to the new customer. Therefore a mixed decision/customer deployment is unsupported and must not receive traffic.

## Rollback

If deployment or validation fails, switch both services back together to their previous versions, again with no traffic between versions. Retain databases and queued events; this change does not alter either, so no data rollback or event replay is needed.
