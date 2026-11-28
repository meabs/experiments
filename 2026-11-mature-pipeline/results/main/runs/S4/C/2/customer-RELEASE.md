# Customer release

## Rollout order

Deploy `notifier` fully first, one instance at a time. Its daily cap must be active before deploying `customer`, also one instance at a time. No queue drain or atomic switch is required.

## Mixed-version behaviour

The customer API and `offer.queued {customerId, offerId}` event are unchanged. Old and new customer instances can therefore share the existing database and run together. New customer instances reject `implied` consent for both `consent.check` and `offer`; old instances may still enqueue offers for legacy customers until they are replaced. The notifier accepts the unchanged event from either customer version, and the new notifier's daily cap applies to those events.

## Rollback

Roll back by routing traffic back to the previous customer version, or the previous notifier version, one instance at a time. No schema rollback or event replay is needed. Queued events remain valid across versions. If customer is rolled back, old behaviour may again enqueue implied-consent offers; keep the new notifier deployed to retain the daily cap. If notifier is rolled back, the customer remains compatible, but the notifier's daily cap is no longer enforced by that old version.
