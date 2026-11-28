# Decision CHG-100 rollout

## Rollout order

Deploy the new decision instances before deploying the customer CHG-100 version. The release pipeline should complete the decision rollout before the customer rollout begins. No drain is required: decision is stateless and does not consume or publish queued events. No atomic switch is required; instances may be upgraded one at a time.

## Mixed-version behavior

The new decision version returns the existing `score` plus the additive `reason` field. Old customer instances ignore the additional field, so old and new decision instances can serve traffic during the decision rollout. The customer change must wait until decision is fully upgraded, because the new customer version relies on `reason`; after that point, old customer instances remain compatible with the new decision response.

## Rollback

If the customer rollout fails, stop it and roll customer instances back to the old version first; then decision may be rolled back one instance at a time. This ordering prevents a new customer instance from receiving a response without `reason`. If only decision has been deployed, it can be rolled back directly because old customer instances tolerate the additive field. Persistent databases and queued events need no migration or replay.
