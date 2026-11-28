# Decision release

## Rollout order

1. Roll out the new `decision` version one instance at a time until every decision instance is new.
2. Roll out the CHG-100 `customer` version one instance at a time after that. The customer team should declare `deploy_after: ["decision"]` in its release plan; this service has no queue or atomic-switch requirement.

## Mixed-version behavior

The new decision version returns the existing `score` plus the additive `reason` field. Old customer instances continue to read `score` and ignore `reason`, so mixed old/new decision instances are safe during step 1. Once customer is upgraded, its new instances can use `reason` from every decision instance.

## Rollback

If the decision rollout fails, stop it and route traffic back to old decision instances; no database or event migration is involved. If customer rollout fails, roll customer back to its old version while retaining the new decision version, which remains compatible. Do not roll decision back while new customer instances are running unless customer is first rolled back to the old version; otherwise the new customer version may receive a response without `reason`.
