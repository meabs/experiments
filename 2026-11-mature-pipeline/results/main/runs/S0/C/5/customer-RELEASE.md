# Release plan

`customer` has no ordering or atomic-cutover dependency on `decision`. The default pipeline rollout is safe: deploy one instance at a time in alphabetical order, with `customer` before `decision` when both services are in this release. Deploying `decision` first is also compatible.

While old and new instances overlap, customer sends the unchanged `income` and `amount` request. It accepts the existing decision response and returns `{decision, score}`, or copies `reason` when the decision response includes it. Old customer instances ignore the additive `reason` field returned by new decision instances. There are no database migrations or queued-event format changes.

To roll back, stop replacing instances and deploy the previous customer version one instance at a time. Both versions use the same unchanged database schema and can be mixed during rollback. If `decision` is also rolled back, either order remains compatible; any newly supplied reason is simply absent from responses handled by the old customer version.
