# Decision release

## Rollout order

1. Roll out the new decision version one instance at a time until every decision instance is new and healthy.
2. Only then begin the customer CHG-100 rollout. Do not use an atomic cross-service switch; the services remain independently deployable.

## Mixed-version behavior

The new `decision.score` response adds `reason` and retains the existing `score` field and calculation. Old customer instances ignore the additional field, so a rolling decision deployment is safe. The customer rollout must wait until decision is fully new, because a new customer instance may consume `reason` while an old decision instance does not provide it.

## Rollback

If decision rollout fails, stop and roll decision instances back to the previous version; no database or queued-event migration is involved. If customer rollout fails, roll customer back first. The new decision version can remain deployed during that rollback because old customer versions accept the additive response. If decision itself must be rolled back after customer has started, roll customer back before or together with it, then verify traffic is served only by compatible versions.
