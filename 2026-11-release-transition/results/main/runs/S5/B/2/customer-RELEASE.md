# Release plan

## Rollout order

Deploy the new `customer` and `decision` versions atomically: switch every instance of both services at the same time, with no traffic served between the old and new versions. There is no required ordering relative to `ledger` or `notifier`, and no queue drain is required.

The atomic constraint is required because `decision.score` changes from a 0–100 scale to a 0–1000 scale, while its response contains no scale/version marker. The new customer applies the 0–1000 thresholds (approve at 600, refer at 400) and returns the score unchanged.

## Mixed-version behavior

Old and new `customer`/`decision` pairs are each internally compatible: the old pair uses 60/40 on the old scale, and the new pair uses 600/400 on the new scale. A mixed pair is deliberately not admitted, since a numeric score at or below 100 is ambiguous without a scale marker.

Existing customer data, ledger events, and notifier queue contents are unchanged. New instances run the existing customer schema migrations, which are idempotent.

## Rollback

If the release fails, atomically switch all `customer` and `decision` instances back to the previous versions, with no traffic between versions. Preserve the databases and queued events; neither service requires a data rollback or event replay for this change. Do not roll back only one of the two services.
