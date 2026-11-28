# Release plan

Switch `customer` and `decision` together, with all instances changed before either service receives traffic. There is no database migration or queued-event change for this release, so existing data and events remain valid.

While the old versions run, the old decision response remains `{score}` and the old customer continues to work. The new decision response is additive (`{score, reason}`), and the paired new customer forwards `reason` from that response. Keeping the switch atomic prevents a new customer instance from being paired with a legacy decision instance during rollout.

If the rollout fails, stop traffic to the changed pair and restore the previous customer and decision versions together. No data or queued events need to be reverted; retry or process them with the restored versions. A rollback must also be atomic so the old customer is not left talking to the new customer contract.
