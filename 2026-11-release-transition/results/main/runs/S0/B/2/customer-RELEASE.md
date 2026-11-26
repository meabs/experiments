# Customer release plan

## Rollout order

No dependency or coordinated switch is required. Deploy `customer` one instance at a time in the normal alphabetical release order, allowing old and new instances to serve traffic together. The `decision` service may be deployed independently; there is no need to drain queued events.

## Mixed-version behavior

The new customer accepts the existing decision response containing only `score` and returns the existing `{decision, score}` shape. When a newer decision instance supplies the optional `reason`, the new customer copies it into `apply`'s response. Older customer instances ignore that additional decision-response field and continue returning their existing response shape. No database schema or queued-event format changes are made.

## Rollback

If the rollout fails, stop and route traffic back to the previous customer version, then roll back remaining instances one at a time. The previous version remains compatible with both old and new decision responses because it uses only `score`; no database or event cleanup is required. A partial rollback is safe because the two customer versions can run concurrently.
