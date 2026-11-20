# Highly available GKE platform with Cloud SQL analytics feed: design v2

## 1. Targets and SLO

- End-to-end monthly availability SLO is 99.95% for successful requests, measured at the global load balancer. Availability budgets are allocated across load balancing, GKE, Cloud SQL, dependencies, and planned maintenance; component targets are not multiplied to claim the end-to-end SLO.
- The platform must tolerate loss of one zone without operator action.
- Regional recovery has a 15-minute RTO and 5-minute RPO, measured in rehearsals. These are objectives, not guarantees, until demonstrated by test results.
- Peak traffic is approximately 5,000 requests/second. The eight-person team uses managed services and keeps the recovery region substantially pre-provisioned.

## 2. GKE topology and capacity

- A regional GKE Standard cluster runs in europe-west2, with control-plane replication and node pools across all three zones.
- Separate system and application pools use the Regular release channel. Upgrade compatibility is tested before upgrades, and a documented maintenance exclusion window protects peak business periods.
- The VPC-native cluster uses private nodes, restricted control-plane access, and regional Cloud NAT.
- The pod secondary range is sized from the selected `maxPodsPerNode`, maximum autoscaled node count, surge capacity, and growth headroom—not an assumed `/22`. The resulting range and expansion plan are recorded in the infrastructure repository.
- Six application replicas use required zone topology spreading. Required hostname anti-affinity is used only where node capacity proves it feasible; otherwise the placement guarantee is provided by tested topology constraints and capacity policy.
- PDBs use `minAvailable: 5` for six-replica tiers. Surge upgrades use `maxSurge: 1` and `maxUnavailable: 0`, with sufficient spare capacity for voluntary disruption and zone loss.
- Capacity tests demonstrate normal peak operation, zone-loss operation, upgrades, and autoscaler convergence without breaching the availability SLO.

## 3. Traffic and regional recovery environment

- A global external Application Load Balancer has healthy backends in both regions and uses health-based regional failover. The client DNS entry has a low, tested TTL; DNS caching is not the primary failover mechanism.
- The recovery region (europe-west1) has pre-provisioned GKE capacity, networking, NAT, load-balancer backend configuration, manifests, image access, secrets, configuration, observability, and IAM. Its capacity and deployment process are tested regularly.
- Health checks verify application readiness and dependency state, not merely process liveness. Failover policy prevents routing writes to an unpromoted database.

## 4. Cloud SQL

- Cloud SQL for PostgreSQL uses regional HA for automatic in-region failover. Its HA standby is not used for queries.
- Dashboards use a separately provisioned in-region read replica, sized for reporting load and monitored for replication lag, storage, and failure. Dashboard behavior during replica lag or failure is documented.
- A cross-region read replica in europe-west1 supports regional recovery. Its lag is continuously monitored and alerts before the 5-minute RPO threshold.
- The recovery runbook fences or stops writes in the old region to prevent split brain, verifies replica lag and the RPO acceptance criterion, promotes the cross-region replica, validates the new write endpoint, and only then enables writes and traffic in the recovery region.
- Backups and PITR are enabled. Restore time is a measured, database-size-dependent objective recorded from rehearsals; no fixed “five minutes regardless of size” assumption is used.

## 5. CDC to BigQuery

- Datastream uses the supported PostgreSQL logical-decoding configuration, with WAL retention, storage impact, and replication-slot monitoring. It is configured and tested so CDC cannot allow unbounded WAL growth or endanger the primary.
- The target freshness objective is five minutes, with alerts at three minutes. BigQuery merge processing is idempotent.
- During regional recovery, Datastream is stopped or fenced against the old source, then repointed or reconnected to the promoted Cloud SQL primary using a documented procedure. CDC continuity, duplicate handling, and BigQuery freshness are validated before recovery is declared complete.

## 6. Security and observability

- Workloads use Workload Identity Federation for GKE with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only pipeline-built images.
- BigQuery personal-data columns use policy tags and customer-managed encryption keys.
- Dashboards cover request success rate and latency, error-budget burn, per-zone capacity, autoscaler state, Cloud SQL and cross-region replica lag, WAL retention, Datastream status/freshness, BigQuery staleness, and load-balancer backend health.
- Alerts and runbooks cover write fencing, promotion, stale replicas, CDC interruption, and recovery-region readiness.

## 7. Testing and acceptance

- Quarterly game days test zone loss, upgrades, autoscaling, read-replica failure, and CDC degradation.
- At least annual full regional recovery rehearsals test, end to end: write fencing, replica-lag verification, Cloud SQL promotion, recovery-region deployment, secrets/configuration, Datastream reconnection, load-balancer failover, write validation, and BigQuery freshness.
- The 15-minute RTO and 5-minute RPO are accepted only when demonstrated by rehearsal evidence. Restore/PITR timings, failover timings, CDC recovery, and error-budget performance are recorded and used to revise capacity and runbooks.