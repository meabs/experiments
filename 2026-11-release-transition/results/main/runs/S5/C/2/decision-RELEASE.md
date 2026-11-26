# Decision CHG-105 rollout

## Rollout order

1. Prepare the customer CHG-105 and decision releases together.
2. Switch every customer and decision instance together, with no traffic between the old and new versions. The release is atomic across the two services.

An ordinary one-instance-at-a-time rollout is unsafe because the old customer thresholds apply to 0..100 scores while the new decision contract returns 0..1000. No database migration or event drain is needed: decision is stateless, and its contract is synchronous.

## Mixed-version behavior

There is no mixed-traffic period. Before the switch, old customer instances call old decision instances and use the legacy scale. After the switch, new customer instances call new decision instances and use the finer scale. Existing databases and queued events remain valid and untouched.

## Rollback

If either service fails validation, stop the combined rollout and switch both services back together. Do not roll back decision independently while the new customer is active, or roll back customer independently while the new decision is active: either pairing would mix incompatible score scales. No database or queued-event rollback is required.
