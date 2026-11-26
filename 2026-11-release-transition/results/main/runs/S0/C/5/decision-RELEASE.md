# Decision release

## Rollout order

Deploy all `decision` instances first, one at a time. Once `decision` is fully
deployed, roll out `customer`. The customer release must declare
`deploy_after: ["decision"]`; this service has no prerequisite because the
provider change is backward-compatible.

## Mixed-version behavior

The new decision version keeps the existing `score` field and adds `reason`.
Old customer instances only read `score`, so they continue to work while old
and new decision instances coexist. After decision is fully deployed, new
customer instances can rely on `reason` while any remaining old customer
instances continue to ignore it. No database migration or queued event format
change is involved.

## Rollback

If the decision rollout fails, stop and roll back the changed decision
instances; the old decision version remains compatible with old customer
instances. If customer rollout later fails, roll customer back independently;
the deployed decision version remains compatible because its added response
field is optional to old customer versions. Existing databases and queued
events require no rollback action.
