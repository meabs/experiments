# Notifier rollout

## Order

Switch customer and notifier atomically, with no traffic between old and new versions. This prevents an old notifier from consuming retained events under the new customer's explicit-opt-in rule.

## Mixed versions

The migration creates `offer_caps` with `IF NOT EXISTS`; existing `sent` rows and queued events are retained. New notifier instances continue consuming the old event shape, re-check explicit marketing consent, and count existing `sent` rows for the current platform day, so a restart does not reset the cap. New instances return the additive `capped` field; old clients that read only `count` and `ticks` remain compatible. The drop total is cumulative per customer, while the two-send limit resets at `platform tick / 100`.

## Rollback

Roll back customer and notifier together. Do not delete or rewrite `sent` or `offer_caps`; leave queued events retained for retry. The coordinated rollback avoids exposing the old notifier to the new customer rule.
