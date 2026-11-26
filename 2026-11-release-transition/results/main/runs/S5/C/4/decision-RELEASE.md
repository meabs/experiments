# Release plan

Deploy the new `decision` and `customer` versions as one atomic cutover. All
instances of both services must be switched together, with no traffic routed
between the old and new versions during the switch. No service needs to wait
for queued events to drain, because this change does not add or change event
schemas or database data.

While the old versions run, they continue to use the 0–100 score and its old
customer thresholds. Once the cutover is complete, the new decision service
returns 0–1000 scores and the new customer service uses the corresponding
finer-scale thresholds. A mixed decision/customer pair is not compatible:
the old customer would apply old thresholds to new scores, and the new
customer would apply new thresholds to old scores. The atomic cutover prevents
either mixed state from receiving traffic.

If the rollout fails, stop it and restore the old versions of both services as
a single atomic rollback, again with no traffic between versions. Roll back
the pair even if only one service appears unhealthy; otherwise score-based
application decisions could be inconsistent. Databases and queued events can
be retained because this release makes no persistent or event-format changes.
