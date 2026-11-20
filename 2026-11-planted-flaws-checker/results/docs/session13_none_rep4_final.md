# Highly available GKE platform with a Cloud SQL analytics feed: design v4

Written by Agent I, the platform lead.

## 1. Targets and availability model

- The end-to-end customer-facing availability SLO is 99.95% per calendar month (about 22 minutes of error budget), measured as successful, correctly served requests at the global load balancer.
- The error budget is allocated across the application, GKE, load balancing, Cloud SQL, networking, and regional-recovery operations. The team will not infer the end-to-end SLO by assigning 99.95% independently to each dependency; the allocation and dependency assumptions will be recorded and reviewed against measured service-level objectives.
- The platform must survive loss of one zone without operator action.
- Loss of a whole region requires a documented and rehearsed recovery in a second region, with a 15-minute RTO and a 5-minute RPO, subject to the tested database-replication and traffic-cutover procedures.
- Peak traffic is about 5,000 requests per second. The team is eight engineers on a managed-service budget.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled. Node pools have sufficient maximum size and surge headroom for the tested application baseline, a zone loss, and upgrades.
- The VPC-native pod secondary range will be sized from the configured maximum pods per node, maximum nodes, upgrade surge, the selected application baseline, and growth headroom. A /18 is the initial planning size and must be validated against the selected GKE alias-IP settings; it is not treated as a universal fixed requirement.
- The cluster has private nodes. Access to the control-plane endpoint is limited to authorized networks. Internet egress uses Cloud NAT on a regional Cloud Router.
- The cluster uses the Regular release channel (or Stable if it supports all required features), with a tested upgrade policy and a weekly maintenance window on Sunday from 02:00 to 06:00 local time.

## 3. Capacity

- Each API pod is initially estimated to serve about 800 requests per second. The deployment baseline will be at least eight replicas, giving an initial nominal capacity of about 6,400 requests per second; the actual baseline is set by load-test results and must provide measured headroom above the 5,000-requests-per-second peak.
- Capacity tests must include peak-plus-headroom traffic, loss of one zone, autoscaler delay, rolling upgrades, and realistic dependency behavior. The tested replica baseline and per-pod capacity are not treated as guarantees until those tests pass.
- Each zone's node pool is sized for the tested baseline and about 60% utilization at peak. After loss of one zone, the remaining zones are sized and autoscaled to carry the traffic without exceeding the application's tested capacity; the stated 90% utilization is a validation target, not a guarantee.
- Autoscaler limits, quotas, pod requests, pod secondary ranges, and surge capacity are tested for normal peak, peak plus headroom, zone loss, and rolling upgrades. They are sized for the selected baseline rather than assuming six replicas.

## 4. Workload placement and disruption

- Stateless tiers run the load-tested baseline of at least eight replicas, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Preferred hostname anti-affinity reduces same-node concentration; placement and capacity tests verify the actual zone and node-failure behavior.
- Each tier has a PodDisruptionBudget that permits controlled maintenance while preserving service capacity (initially `minAvailable: 7` for eight replicas). The value is reviewed with the zone-loss and upgrade tests and must not block necessary voluntary drains.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to available quota and capacity.

## 5. Traffic and regional failover

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use an application readiness/health endpoint that represents the ability to serve traffic, including required dependency readiness, rather than merely process liveness. Connection draining is 60 seconds.
- Regional selection and failover use the load balancer's documented health-based failover/routing behavior, not a one-hour DNS change. The configuration, detection time, backend health behavior, and cutover are tested to meet the 15-minute regional RTO.
- DNS, if used for the service name, has a TTL and managed-routing behavior compatible with the RTO; DNS caching is not relied on as the sole failover mechanism.

## 6. Database

- The transactional database is Cloud SQL for PostgreSQL in europe-west2 with high availability enabled: a primary in one zone and a standby in another, with automatic same-region failover. Automated backups and point-in-time recovery are enabled.
- The HA standby is not used as a read endpoint. Dashboard queries use a separately provisioned, supported Cloud SQL read replica (or an explicitly approved BigQuery path), sized and monitored independently. Its lag, failure behavior, and dashboard fallback are documented.
- A cross-region read replica in europe-west1 is the regional-recovery target. The recovery runbook verifies replication lag, fences or stops writes to the old primary, promotes the replica, updates application database configuration, validates data and application health, and then enables the second-region backend.
- Replication lag and the achievable data-loss window are continuously monitored. The runbook and regular recovery rehearsals must demonstrate the 5-minute RPO; if lag exceeds the bound, recovery is escalated rather than claiming the RPO was met.
- Backup/PITR restore time is measured for the actual database size and documented with a tested RTO/RPO. Restore time is not assumed to be five minutes regardless of database size. Restores include integrity, application, and backup validation before service use.

## 7. Change data capture to BigQuery

- Datastream reads committed changes from the Cloud SQL primary through a supported logical-decoding configuration and writes them to BigQuery. The enforceable freshness objective is that each committed change reaches the usable BigQuery destination within five minutes, measured from commit time; alerts fire at three minutes.
- A breach of the five-minute objective triggers documented escalation, investigation of Datastream lag and destination failures, and recovery actions such as clearing backpressure, restoring the stream, or replaying/backfilling from the source. Persistent breaches are treated as an operational incident and are not hidden by the destination staleness setting.
- Replication slots, WAL retention, storage growth, CPU, and primary impact are monitored. Backpressure and slot recovery procedures prevent CDC from endangering primary availability or exhausting storage.
- CDC behavior during same-region failover and regional promotion is documented and tested, including fencing the old primary, reconnecting to the promoted primary, duplicate and ordering handling, and any replay/backfill required. The resulting CDC data-loss/freshness behavior is included in the recovery procedure.
- The BigQuery destination's 15-minute staleness limit is a cost-control ceiling only; it does not relax or replace the five-minute committed-change freshness objective. Events are applied idempotently (for example, merge by primary key with suitable change ordering) so replayed events do not create duplicate rows.

## 8. Security

- Workloads reach Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default, and Binary Authorization admits only images built by the approved pipeline.
- Columns containing personal data are covered by policy tags in BigQuery, and datasets use customer-managed encryption keys.

## 9. Observability

- Service-level indicators are request success rate and latency measured at the load balancer. Alerts cover error-budget burn over one-hour and six-hour windows.
- Dashboards show Cloud SQL primary/replica and cross-region replication lag, CDC freshness and slot/WAL/storage health, BigQuery staleness, node-pool capacity per zone, quotas, and autoscaler state.
- Alerts and runbooks cover regional backend health, failover progress, database fencing/promotion, and restoration validation.
- CDC alerts distinguish the three-minute warning from the five-minute objective breach and include escalation and recovery/backfill status.

## 10. Testing and operations

- A zone-failure game day occurs quarterly, including capacity, pod placement, autoscaling, application health checks, and load-balancer health behavior.
- A full regional recovery rehearsal occurs at least annually, including database promotion, fencing, CDC reconnection/backfill, traffic cutover, and validation of the 15-minute RTO and 5-minute RPO.
- Restore/PITR tests, read-replica failure tests, rolling upgrades, and CDC backpressure/recovery tests are performed on a documented schedule. Each exercise produces a written report, measured results, and tracked corrective actions.
- The build is blocked until the capacity, failover, replication, restore, and CDC tests validate the targets stated above, including the selected replica baseline, peak-plus-headroom capacity, one-zone-loss capacity, autoscaler behavior, and the enforceable five-minute CDC freshness objective.