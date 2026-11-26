# Release plan

## Rollout order

Deploy the new `decision` and `customer` artifacts as one atomic release. The pipeline must switch every instance of both services together, with no requests routed between the old and new versions during the switch. There is no event-drain requirement: decision is stateless and publishes or consumes no events.

## Version compatibility

Before the switch, the old pair continues to use the old 0–100 score and 60/40 customer thresholds. After the switch, the new pair uses the 0–1000 score and 600/400 thresholds. Do not run a new customer with an old decision or an old customer with a new decision: either mixed pair would make approval decisions incorrect because the numeric scales differ.

The request and response shape remains unchanged (`score {income, amount}` -> `{score}`), and decision has no database schema or queued-event state to migrate.

## Rollback

If health checks or decision sampling fail, stop the atomic release and switch all `decision` and `customer` instances back together to the previous artifacts, again with no traffic between versions. Existing databases and queued events are retained; neither service has release-specific state to undo. A rollback must not downgrade only one of the two services, for the same score-threshold compatibility reason.
