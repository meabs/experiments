# Notifier rollout

Switch `customer` and `notifier` as one atomic release: all instances of both
services change together and no traffic is admitted between the two switches.
This is required because old notifier instances do not enforce the new daily
cap; it prevents them from processing offers after the customer marketing rule
changes. Both versions still publish/consume the existing
`offer.queued {customerId, offerId}` event.

The notifier migration creates the additive `offer_caps` table. New instances
send at most two offers per customer per platform day (`tick / 100`), and the
`sent` response keeps `count` and `ticks` while adding `capped`. The shared
`sent` and `offer_caps` data is retained. Outside the atomic switch, old and
new versions remain compatible at the event boundary; during the switch there
is no mixed customer/notifier traffic.

If either service rollout fails, roll both services back as one atomic unit.
Preserve the database and queued events; already-sent rows and cap counters are
never removed. After recovery, verify `sent` counts and capped totals before
retrying the combined rollout.
