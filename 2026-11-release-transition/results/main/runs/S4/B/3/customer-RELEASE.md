# CHG-104 rollout

## Rollout order

Deploy `notifier` completely before deploying `customer`. Within each service, deploy instances one at a time and wait for health before moving to the next instance. No atomic switch or queue drain is required.

## Mixed-version behavior

The customer event contract is unchanged: `offer.queued` still contains `customerId` and `offerId`, so old and new customer and notifier instances can consume or produce the same messages. During the customer rollout, old customer instances may still queue offers for `implied` consent; the fully deployed new notifier applies its daily cap to those events. New customer instances stop both queuing those offers and reporting them as allowed through `consent.check`. Explicit-consent offers continue to work throughout.

## Rollback

Rollback either service one instance at a time, keeping the unchanged event schema and existing database rows. Customer can be rolled back to restore its previous implied-consent behavior; notifier can be rolled back independently without requiring a queue drain. If notifier is rolled back after customer, the old notifier remains wire-compatible, but its new daily-cap behavior is no longer present. Re-deploy the new notifier to restore the cap, then complete or retry the customer rollout as needed.
