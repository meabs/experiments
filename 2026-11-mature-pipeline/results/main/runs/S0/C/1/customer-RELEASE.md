# Customer release

## Rollout order

No dependency on the decision rollout is required. The release pipeline may deploy customer in its normal alphabetical, one-instance-at-a-time order, before or after decision. No queue drain or atomic switch is needed.

## Mixed-version behavior

New customer instances accept the existing `decision.score` response containing only `score`, and also copy `reason` when a newer decision instance provides it. Old customer instances ignore the additional decision field. Therefore old and new customer and decision instances can serve traffic together.

The change adds no database tables, migrations, events, or request fields.

## Rollback

If the rollout is rolled back, route traffic back to the previous customer version. It remains compatible with both score-only and reason-bearing decision responses because it already ignores unknown response fields. No database cleanup or queued-event replay is required.
