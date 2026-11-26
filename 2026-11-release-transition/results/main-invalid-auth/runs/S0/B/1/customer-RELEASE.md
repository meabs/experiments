# Customer release

## Rollout order

There is no service dependency constraint for this change. Use the normal one-instance-at-a-time rollout; if the pipeline uses the default estate order, customer is deployed alphabetically before decision. Customer does not need to wait for decision to be fully deployed, and the two services do not need an atomic switch.

## Mixed-version behavior

The new customer accepts the existing decision response containing `score` and also copies `reason` when a newer decision returns it. An old customer ignores the additional decision field and continues returning its original `decision` and `score` response. Therefore old and new customer and decision instances can serve traffic in any combination during rollout. No database schema or event format changes are made.

## Rollback

If the customer rollout is unhealthy, stop it and route traffic back to the old customer instances. The old customer is compatible with both old and new decision responses. If decision is rolled back independently, the new customer remains compatible because `reason` is optional. Existing database contents and queued events require no migration or replay for this change.
