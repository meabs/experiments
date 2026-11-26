# Customer release

## Rollout order

The decision service must be fully deployed before customer is deployed. Decision instances may be replaced one at a time; once all decision instances serve the 0–1000 score scale, replace customer instances one at a time. No event drain is required because this change does not publish or consume events.

## Mixed-version behavior

During the decision rollout, old customer instances continue to call both old and new decision instances using the unchanged `score` operation and response shape. During the customer rollout, old and new customer instances can run together: they use the same database schema, request fields, response fields, and synchronous call. New customer instances apply the 600/400 thresholds and return the decision score unchanged; old instances retain their legacy threshold interpretation until replaced.

## Rollback

If the customer rollout fails, stop it and restore customer instances to the previous version. If the decision rollout must also be reverted, restore customer first, then decision, keeping the old customer threshold interpretation paired with the old 0–100 decision scale. Existing database contents and queued events require no migration or replay.
