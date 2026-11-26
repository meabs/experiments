# Decision release

## Rollout order

Deploy the new `decision` instances first and complete that rollout before deploying the customer CHG-100 change. No atomic switch is required, and no queued-event drain is required because decision is stateless and publishes no events.

## Mixed-version behavior

During the decision rollout, old and new instances both accept the existing `score {income, amount}` request. Both return `score`; new instances additionally return `reason` in the form `ratio <n>%`. Old customer instances ignore the extra field, while the customer change can consume it after decision is fully deployed. There is no database migration or persistent message format to coordinate.

## Rollback

If the rollout fails, route traffic back to the old decision instances. Existing callers continue to work because `score` is unchanged; the only lost capability is the additive `reason` field. If customer CHG-100 has already been deployed, roll it back before or alongside decision if it requires `reason`, then retry decision later. No database or queued-event rollback is needed.
