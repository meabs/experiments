# Customer release

## Rollout order

Deploy and switch `customer` and `decision` atomically: all instances must be switched together, with no traffic routed between the old and new pair. No queue drain is required because the changed interaction is synchronous and `decision` is stateless.

## Mixed-version behavior

Do not run an old customer instance with a new decision instance, or a new customer instance with an old decision instance. The old customer interprets scores on the old 0–100 scale, while this customer interprets the new 0–1000 scale. The atomic switch avoids that incompatible mixed-version window. Existing customer databases and queued events are unaffected; the customer schema and event contracts are unchanged.

## Rollback

If the release fails, stop routing to the new pair and atomically switch both services back to their previous versions. Do not roll back only one service. The database and queued events remain usable because this change has no migration and changes no event shape.
