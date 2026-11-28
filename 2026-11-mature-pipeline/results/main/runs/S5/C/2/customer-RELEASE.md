# Customer release

## Rollout order

Deploy the new customer and decision versions as one atomic release group. Switch every instance of both services together, with no traffic routed to a mixed-version pair. No queue drain is required: customer does not change its database schema or event format, and existing events remain valid.

## Mixed-version behavior

Do not serve traffic while only one service has switched. The old customer expects decision scores on the 0–100 scale, while the new customer expects the 0–1000 scale; either mixed pair would classify applications incorrectly. Outside the atomic switch, customer continues to use the existing database and published event formats unchanged.

## Rollback

If the release fails, switch all customer and decision instances back together to their previous versions, again with no traffic between versions. The rollback is database- and queue-safe because this change has no schema migration and does not alter event payloads.
