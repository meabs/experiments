# Customer release plan

## Rollout order

Deploy customer independently, one instance at a time, using the normal pipeline order. No `deploy_after` or `atomic_with` constraint is required, and queued events do not need to be drained before deployment.

## Mixed versions

New customer instances treat only `explicit` consent as marketing permission. They return `allowed=false` for `implied` and do not publish an event for those offers. They continue to publish the existing `offer.queued` event, with the unchanged `customerId` and `offerId` fields, for explicitly consenting customers.

During a partial rollout, old customer instances may still publish offers for legacy `implied` consent; new and old notifier instances can consume those events because the event contract is unchanged. The notifier's daily cap therefore remains the notifier's responsibility regardless of which customer version emitted an event.

## Rollback

Rollback can switch customer instances back one at a time. The old version can read the unchanged customer table and process retained events. After rollback, old customer instances may again queue offers for `implied` consent; any notifier version still deployed will process those events according to its own behavior and cap. No database migration or event replay is required.
