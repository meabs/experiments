# Release plan

Deploy `customer` and `decision` atomically: switch all instances of both services together, with no traffic between the old and new pair. There is no meaningful ordering within the pair because the published score scale and the customer's interpretation of it change together.

While the old pair is serving, scores are 0–100 and the old customer thresholds apply. Once the pair is switched, scores are 0–1000 and the new customer thresholds apply. Do not allow a mixed pair: an old customer would treat a new 0–1000 score as if it were 0–100 and could approve incorrectly; a new customer receiving an old 0–100 score would decline incorrectly.

If the rollout fails, leave the new pair out of service and continue with the old pair. Roll back `decision` and `customer` together, all instances at once, before sending traffic to them. Databases and queued events need no cleanup because this change is stateless and changes no persisted schema or event payload.
