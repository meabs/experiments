# Release plan

Deploy `customer` independently using the pipeline default: services are ordered alphabetically when no constraints apply, and instances are switched one at a time. There is no required ordering relative to `decision`, no atomic switch, and no need to drain queued events first.

## Mixed versions

The new customer accepts the existing `decision.score` response containing only `score`, so it works while old decision instances are serving traffic. It also copies `reason` when a new decision instance returns it. Old customer instances continue to return their existing `{decision, score}` response and ignore the additive `reason` field returned by new decision instances. No database schema or event format changes are involved.

## Rollback

If the rollout fails, stop switching instances and route traffic back to the old customer version. The old version remains compatible with the unchanged database and queued events; no data migration or event replay is needed. If some new instances were already switched, they can be rolled back independently while old and new decision instances continue to run side by side.
