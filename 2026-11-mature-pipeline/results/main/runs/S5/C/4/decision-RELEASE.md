# Release plan

Deploy `decision` and `customer` as one atomic cutover, with all instances switched together and no traffic routed between the two versions. Before the cutover, the old decision and old customer continue to use scores from 0 to 100. After it, the new pair uses scores from 0 to 1000, with customer thresholds expressed on that finer scale.

While old and new instances exist during preparation, keep traffic on the old pair; do not mix an old customer with a new decision or a new customer with an old decision. The score response remains the same operation and field (`score`), but its range is version-dependent, so the pair is not independently compatible during a rolling transition.

If validation fails, route traffic back to the old pair and roll back both services together. Do not roll back only one service, and retain the existing database and queued-event contents; this change does not require a data migration or event replay.
