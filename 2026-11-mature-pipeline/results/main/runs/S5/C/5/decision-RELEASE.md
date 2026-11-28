# Release plan

## Rollout order

Deploy `decision` and `customer` as one atomic release group. Switch every instance of both services together, with no traffic sent to a mixed old/new pair. There is no independent alphabetical rollout order for these services because the published score scale and the customer's interpretation of it change together.

## Mixed-version behaviour

Mixed versions must not receive traffic: the old customer interprets scores on the 0–100 scale, while the new customer interprets scores on the 0–1000 scale. The new decision service is stateless and makes no database or queued-event changes, so existing data and events remain valid, but that does not make mixed score semantics safe.

## Rollback

If any health check or rollout step fails, stop the group and restore the previous versions of both services together before resuming traffic. Roll back the customer and decision versions as a pair; do not leave a new customer with an old decision service or vice versa. Keep databases and queued events intact because this change adds no schema migration and changes no event format.
