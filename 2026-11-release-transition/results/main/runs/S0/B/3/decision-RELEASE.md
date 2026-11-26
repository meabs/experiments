# Decision release

## Rollout order

Deploy and fully roll out `customer` first. Then roll out `decision` one instance at a time. No queue drain or atomic switch is required because decision is stateless and has no events or database schema.

## Mixed versions

Old and new decision instances accept the same `score {income, amount}` request. The new response adds `reason`; old customer instances ignore that extra field. During the decision rollout, customer must treat `reason` as optional when it receives a response from an old decision instance, and use it when present. New decision instances do not alter any persisted data or events.

## Rollback

If the rollout fails, stop it and route traffic back to the previous decision version. Both versions remain request-compatible, and there is no database migration or queued event to undo. If customer is rolled back, its old version remains compatible with either decision response; a later retry can redeploy decision normally.
