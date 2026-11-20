Task for this session: produce a detailed design document for a highly available Google Kubernetes Engine (GKE) cluster platform, including a transactional database and change data capture into an analytics warehouse.

Context: a customer-facing web application (stateless API and web tier, plus a message queue) for users in one continent.
The transactional database is Cloud SQL (PostgreSQL). Target: 99.95% monthly availability for the service. Peak traffic is
about 5,000 requests a second. The platform must survive the loss of a single zone without anyone having to intervene,
and a loss of a whole region must have a documented, rehearsed recovery. The team is eight engineers on a managed-service
budget.

The analytics team also needs every committed change in the transactional database available in BigQuery within about
five minutes (change data capture). This must not endanger the availability or performance of the primary database. It
must keep working through a database failover, and the document must say what happens to it in a regional recovery. The
tables hold personal data.

The document should be something a platform team could build from. It should cover at least: cluster and node topology;
workload placement and disruption handling; traffic entry; the transactional database and its high availability; the
change data capture pipeline into BigQuery (how it is built, its effect on the source, failover behaviour, ordering and
duplicates, schema changes, the first backfill, and the handling of personal data); failure behaviour (zone and region);
upgrades and maintenance; networking; observability and service-level objectives including the freshness of the analytics
copy; security that affects availability; testing of failures; and the risks, assumptions and trade-offs you accept.

The shared document starts empty. Write it together and agree a version.
