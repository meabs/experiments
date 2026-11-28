# Release plan

Deploy `decision` and `customer` as one atomic release. Bring up and validate the new versions, then switch all instances of both services together; do not route any traffic to a new version while an old version of the other service remains active. This is required because `decision.score` changes from a 0–100 scale to 0–1000 while customer approval thresholds change correspondingly from 40/60 to 400/600.

During the cutover, old decision and old customer continue to use the old scale. After the switch, new decision and new customer use the new scale. There is no supported mixed-version interval: an old customer would interpret new scores as almost always approved, while a new customer would interpret old scores as declined.

If validation fails or the rollout is interrupted, stop routing to the new pair and atomically restore all instances of both services to their previous versions. No database migration or queued-event format changes are introduced, so retained data and queued events remain usable after rollback.
