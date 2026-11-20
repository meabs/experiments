# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets and availability

- The customer-facing platform targets 99.95% monthly availability (approximately 22 minutes of downtime), measured end to end at the load balancer. This is the platform error budget; component availability targets are inputs, not a claim that independently budgeting three services at 99.95% produces 99.95% end-to-end availability.
- The platform uses GKE, Cloud SQL for PostgreSQL and Google Cloud load balancing.
- It must survive loss of one zone without operator intervention.
- Loss of a whole region requires a documented and rehearsed recovery in a second region, with an objective of 15 minutes RTO and 5 minutes RPO. The asynchronous cross-region database replica means the 5-minute RPO is an objective, not a guarantee.
- Peak traffic is approximately 5,000 requests per second. The team is eight engineers operating managed services.

## 2. Cluster and node topology

- Use one regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools in all three zones.
- Use separate system and application node pools, each with cluster autoscaling enabled. Define and monitor minimum and maximum sizes per pool and per zone.
- Use a VPC-native cluster with private nodes and authorised networks for control-plane access. Egress uses Cloud NAT on a regional Cloud Router.
- Size the pod secondary range for the node and pod autoscaler maxima, surge capacity and growth; use at least a /19 (subject to the approved capacity plan), with expansion and reserved ranges documented. Do not assume a /22 supports 30 nodes at 110 pods per node.
- Use the Regular GKE release channel for production, with a tested maintenance window and upgrade policy. A weekly maintenance window runs on Sunday from 02:00 to 06:00 local time.

## 3. Capacity

- Initially run at least 8 API replicas. The stated 800 requests per second per pod is a planning estimate, not a capacity guarantee; validate capacity, latency and resource requests with load testing.
- Size each zone's node pool and the autoscaler maxima so the remaining two zones can serve peak traffic after loss of one zone, while retaining headroom for pod rescheduling, maintenance and autoscaler latency. Validate this through load testing and a zone-failure game day rather than relying on a 90% utilisation assumption.

## 4. Workload placement and disruption

- Stateless tiers run 8 replicas, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Use required hostname anti-affinity when one replica per node is a requirement; otherwise explicitly document that preferred anti-affinity is only a preference.
- Each tier has a PodDisruptionBudget that permits maintenance while preserving service, initially `minAvailable: 7` for 8 replicas, subject to validation against the zone-failure and capacity plans.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`. Verify that PDBs, capacity and upgrade settings do not prevent planned maintenance indefinitely.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use the application's `/healthz` endpoint, and connection draining is 60 seconds.
- Configure and test documented health-based regional failover at the load-balancer layer. Do not depend on a 3,600-second DNS TTL for the 15-minute RTO. If DNS is retained for any application endpoint, use a suitably low TTL and document resolver-caching limitations.
- Pre-provision, or otherwise guarantee, sufficient tested GKE capacity in the second region; do not rely solely on autoscaler reaction during regional recovery.
- Regional recovery includes routing traffic to the second region, validating capacity and configuration, promoting the database replica, updating application database configuration/secrets, and verifying service health.

## 6. Database

- The transactional database is Cloud SQL for PostgreSQL in europe-west2 with high availability enabled: a primary in one zone and a failover standby in another. The HA standby is not a query endpoint.
- Run analytics dashboards against a separately sized, supported Cloud SQL read replica (or an explicitly approved BigQuery-only design), with documented freshness, lag monitoring, failure behavior and cost limits.
- Use automated backups and point-in-time recovery.
- Maintain a cross-region asynchronous read replica in europe-west1 for regional recovery. Monitor replication lag and validate that it meets the 5-minute RPO objective under representative load. Promote it through a documented, rehearsed runbook.
- Do not assert a size-independent restore time. Define restore RTO/RPO from measured database size, backup throughput and test results, and periodically test restore and point-in-time recovery. A bad migration requires a reviewed recovery procedure, including data-loss assessment and application consistency checks.

## 7. Change data capture to BigQuery

- Configure Datastream using a supported Cloud SQL PostgreSQL logical-decoding configuration. Document replication slots, WAL retention, permissions and resource settings.
- Datastream reads changes from the primary and writes them to BigQuery. The target freshness is five minutes, with an alert at three minutes.
- Monitor slot lag, WAL growth, primary CPU/IO impact, back-pressure and destination errors. Define thresholds and an operational response so CDC cannot exhaust primary storage or otherwise endanger the transactional workload.
- The BigQuery destination's data-staleness limit is 15 minutes, subject to the freshness requirement and cost review. Apply change events idempotently (for example, merge on the primary key) so duplicate events do not create duplicate rows. Validate CDC behavior during regional recovery and failback.

## 8. Security

- Workloads reach Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default, and Binary Authorization admits only images built by the approved pipeline.
- Columns holding personal data are covered by policy tags in BigQuery, and datasets use customer-managed encryption keys.

## 9. Observability

- Service-level indicators are request success rate and latency measured at the load balancer. Alert on error-budget burn rate over one-hour and six-hour windows.
- Dashboards show replica and CDC lag, CDC freshness, logical-decoding slot/WAL usage, read-replica health, node-pool capacity per zone, autoscaler state, load-balancer backend health and regional failover state.
- Alert on capacity headroom, PDB blockage, failed upgrades, Cloud SQL storage/CPU/connection pressure and recovery-replica lag.

## 10. Testing and operations

- Hold a zone-failure game day at least quarterly and a full regional recovery rehearsal at least annually, each with a written report and tracked remediation.
- Rehearsals measure load-balancer failover, two-zone capacity, database promotion time and lag/RPO, application configuration changes, restore performance, CDC slot/back-pressure behavior, BigQuery freshness, and return to normal operation.
- Record measured capacity, restore RTO/RPO, replica promotion time and failover behavior; update the runbooks and declared objectives when measurements change.