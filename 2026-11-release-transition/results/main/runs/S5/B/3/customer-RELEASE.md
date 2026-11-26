# CHG-105 rollout

## Order

1. Roll out the new `customer` instances one at a time, keeping the old customer instances serving traffic until each replacement is healthy.
2. After every customer instance is on the new version, roll out `decision` one instance at a time. The decision rollout must depend on customer being fully deployed; do not send new decision traffic to any old customer instance.

No event drain is needed: this change does not add or change queued events, database tables, or event consumers.

## Mixed versions

The new customer applies 600/400 thresholds to the new 0–1000 decision scale and preserves the score returned by decision. While old decision instances remain, scores in the legacy 0–100 range are interpreted with the legacy 60/40 thresholds. This makes the customer rollout safe one instance at a time and keeps a new customer compatible with an old decision instance.

## Rollback

If the customer rollout fails, stop before deploying decision and restore the affected customer instances.

If the decision rollout fails, keep the new customer version in place, roll decision back to the old version, and then retry or leave customer on the compatibility path. If customer itself must be rolled back after decision has been upgraded, first roll decision back, then roll customer back; never leave an old customer instance receiving the new 0–1000 scores.
