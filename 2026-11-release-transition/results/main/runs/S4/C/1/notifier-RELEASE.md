# Notifier rollout

## Order

First drain the `offer.queued` queue. Then perform one coordinated cutover of all
customer and notifier instances: customer and notifier are an atomic release group,
with no traffic between the old and new groups. This is required because the old
customer can queue offers for legacy `implied` consent and the old notifier does not
enforce the new daily cap.

Before the cutover, each new notifier instance runs its additive startup migrations.
The existing `sent` table is unchanged; `capped` stores the cumulative dropped count
and `offer_customer_lock` coordinates concurrent new-version consumers.

## Mixed versions

There is no served mixed-version interval. Queued events are drained before the
cutover, and both services switch as one group. Afterward, the new customer only
queues offers for explicit consent; the new notifier counts all rows already in
`sent` for the current platform day (`tick / 100`) and accepts only the first two.
Further events increment `capped` without adding a `sent` row. `sent` remains
backward-readable and the event shape remains additive.

## Rollback

If any instance fails, stop the cutover and switch both services back together; do
not leave either new service serving against the other service's old version.
Retain `sent`, `capped`, and queued-event contents. A later retry reruns the
additive migration and resumes from the shared `sent` rows. The old binaries can
read the unchanged `sent` table, while the coordinated rollback avoids accepting
new events in an old-only notifier during this release.
