# Customer release

## Rollout order

Deploy customer first, one instance at a time, using the default alphabetical order. Deploy the decision change after every customer instance is on the new version. No queue drain or atomic switch is required.

## Mixed-version behavior

The new customer accepts both the legacy decision response (scores 0–100) and the new response (scores 0–1000). It applies the new thresholds: 600 and above approves, 400–599 refers, and below 400 declines. Consequently, while old decision instances are still serving, their legacy scores are handled conservatively and never accidentally meet the new approval or referral thresholds. The score field is passed through unchanged.

The old customer remains compatible with the decision response shape, but must not be left serving traffic after the decision rollout starts: its old 60/40 thresholds would interpret new-scale scores incorrectly. The customer rollout order prevents that mixed-scale traffic pattern.

## Rollback

If the customer rollout fails, stop it and route traffic back to the old customer instances; the decision service can remain on its old version. If the decision rollout fails, roll it back to the old decision version; the new customer remains safe and conservatively declines legacy scores. The database and queued events are unchanged by this release, so rollback does not require data reversal or queue draining.
