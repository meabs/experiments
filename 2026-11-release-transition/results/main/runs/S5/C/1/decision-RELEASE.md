# Release plan

Deploy `decision` and `customer` as one atomic release group. Switch every instance of both services together, with no traffic routed between old and new versions during the switch. There is no safe ordering for an independent rollout: the old customer interprets scores as 0–100, while the new customer interprets them as 0–1000; the corresponding mixed-version pair would make approval decisions incorrect in either direction.

While the old pair is serving, `decision.score` remains 0–100. After the atomic switch, the new decision returns 0–1000 and the new customer uses thresholds on that same scale. Existing databases and queued events are unaffected because this change is stateless and changes no event payloads.

If the combined health or compatibility checks fail, stop the rollout and switch all instances of both services back together to the previous versions. Do not roll back only one service; that would recreate the incompatible score-scale pairing. Since the score is computed on demand and no score data is persisted, rollback does not require a data migration or queue rewrite.
