# Customer release

## Rollout order

`customer` and `decision` are an atomic rollout pair. Deploy and switch all instances of both services together, with no traffic routed between the old and new pair. No other service ordering constraint is required.

## Mixed-version behavior

The score response is still the existing `decision.score` response and the `customer.apply` request and response shape are unchanged. The only semantic change is that scores use 0–1000, with customer thresholds of 600 for `APPROVE` and 400 for `REFER`; customer returns the score unchanged. Because an old customer interprets the old 0–100 scale, old and new customer/decision versions must not be paired. The atomic constraint ensures traffic sees either the old pair or the new pair, never a mixed pair. Existing databases and queued events are unaffected.

## Rollback

If either service fails deployment, health checks, or runtime validation, stop the rollout and switch both services back together to the previous versions. Do not roll back only customer or only decision. Preserve the database and queued events; neither service changes their schema or event formats for this release.
