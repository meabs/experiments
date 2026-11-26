# Release CHG-105

## Rollout order

Switch `customer` and `decision` atomically: all instances of both services are switched together, with no traffic between the old and new pair. No service is deployed before the other.

## Mixed-version and data behavior

The `score` response remains a string under the existing `decision.score` operation, and `customer.apply` still returns `{decision, score}`. However, the meaning of the numeric value changes from 0–100 to 0–1000, so an old customer paired with a new decision (or vice versa) would apply incorrect thresholds. The atomic constraint prevents that incompatible pairing while queued events and databases remain unchanged; this change does not add schema or event changes.

## Rollback

If validation or an instance rollout fails, stop the atomic switch and restore the old versions of both services together before sending traffic. If the new pair has already been activated, roll back both services as one unit; never roll back only one service. Existing customer data and queued events are retained and can be processed by the restored versions.
