# Decision release

## Rollout order

1. Deploy and fully verify the customer release first, one instance at a time.
2. Keep decision on its current version while customer instances are mixed old/new.
3. Deploy this decision release one instance at a time after customer is fully deployed.

The customer release must understand both the legacy 0–100 score returned by old
decision instances and the new 0–1000 score returned by this release. This is
required while either service is mixed-version; no traffic pause or atomic switch
is needed.

## Rollback

If the decision rollout fails, stop it and route traffic back to the old decision
instances. The deployed customer version remains compatible with that legacy score
range, so this rollback is safe and queued/database contents need no migration.

If the customer rollout fails, stop it and leave decision on its old version until
customer is fully restored. If the customer release must be rolled back after this
decision release has started, roll decision back to the old version first, then
roll customer back; the customer compatibility behavior makes both score ranges
safe during this sequence. Never remove the old decision instances until the
customer rollout has completed successfully.
