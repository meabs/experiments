# Release plan

Deploy the `customer` and `decision` releases as one atomic switch, with no traffic between the old and new versions. Other services can continue their normal rollout order before or after this pair; neither consumes the decision score directly.

Before the switch, old customer instances call old decision instances and use the 0–100 score thresholds. After the switch, new customer instances call new decision instances and use the corresponding 0–1000 thresholds. Keeping either service old while the other is new would misinterpret the score field, so a partial rollout of this pair is not safe. There is no decision database or queued event state to drain or migrate.

If validation fails, stop traffic to the new pair and atomically roll both services back to their previous versions. Do not roll back only one service; the old customer must be paired with the old decision. Since the service is stateless, no data rollback is required.
