# Release plan

Deploy `customer` atomically with `decision`: switch all instances of both services together, with no traffic between the old and new versions. No queue drain is required; `customer` does not publish or consume an event whose schema changes in this release, and its database schema is unchanged.

While the old versions are serving, `decision.score` remains on the 0–100 scale and `customer.apply` uses the old 60/40 thresholds. During the cutover, both services switch to the 0–1000 score scale and the 600/400 thresholds. This avoids interpreting an old-scale score with new-scale thresholds (or vice versa); the returned `score` remains the value supplied by `decision`.

If validation fails, switch both services back together to their previous versions. Keep the shared databases and queued events unchanged. Because the old and new score values are only used across the coordinated cutover, rollback restores the old pair without requiring data migration or event rewriting.
