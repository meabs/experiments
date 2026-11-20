# Highly available GKE platform with a Cloud SQL analytics feed: design v2

## 1. Targets and service objectives

- Customer-facing stateless web/API service, with peak traffic of approximately 5,000 requests/second.
- Platform service availability objective is 99.95% per month. The error budget and dependency budgets will be allocated across load balancing, GKE, Cloud SQL, networking, and operational procedures; individual managed-service targets are not multiplied as if they directly establish the end-to-end SLO.
- The platform must tolerate loss of one zone without operator intervention.
- Regional recovery target: RTO 15 minutes and RPO 5 minutes, demonstrated by an annual end-to-end rehearsal.
- The design favors managed services and is operated by a team of eight engineers.

## 2. Primary and recovery clusters

- A regional GKE Standard cluster runs in europe-west2, with the control plane replicated across three zones and node pools distributed across all three zones.
- Separate system and application node pools use cluster autoscaling, with explicitly configured per-zone minimums and maximums. Capacity limits are tested against peak load after loss of one zone.
- A warm, continuously maintained GKE deployment and sufficient node capacity are provisioned in the recovery region, europe-west1. Application configuration, secrets, images, policies, and load-balancer backends are maintained there rather than created during an outage.
- The clusters use VPC-native networking and private nodes. Control-plane access is restricted to authorized networks. Internet egress uses regional Cloud NAT.
- The pod secondary range is sized from the actual GKE alias-IP allocation model and configured maximum pods per node, including system-pod allocation, maximum autoscaled node count, and growth headroom. It is not fixed at /22; IP planning will select a sufficiently large range (for example /19 or larger where required) and reserve a documented expansion path.

## 3. GKE release and maintenance

- GKE uses the Regular release channel (Stable may be selected if it supports all required features), not Rapid. Application compatibility is tested before upgrades.
- A weekly maintenance window is configured, and upgrades use surge capacity with maxSurge 1 and maxUnavailable 0 where supported.
- Workload rollouts and upgrades are tested in both regions.

## 4. Capacity and workload placement

- Each API pod currently serves approximately 800 requests/second. Six replicas provide capacity above the 5,000-request/second peak, subject to load testing and resource limits.
- Application replicas are spread across zones using topology spread constraints with maxSkew 1 and DoNotSchedule. Preferred hostname anti-affinity is used, with capacity checks ensuring replicas do not share nodes when required.
- Capacity planning includes node and pod overhead, system workloads, autoscaler limits, surge nodes, and the loss of one zone. The remaining zones must meet peak demand without relying on approximately 90% sustained utilization; this is validated in load and zone-failure tests.
- PodDisruptionBudgets permit at least one voluntary disruption (for example, minAvailable 5 of 6) while preserving the tested availability requirement. PDBs must not block planned maintenance indefinitely.

## 5. Traffic and regional recovery

- A global external Application Load Balancer has health-checked backends in both regions. Health checks include application readiness and dependency readiness, not merely process liveness.
- Regional recovery does not depend on a 3,600-second DNS TTL. The recovery runbook first promotes the Cloud SQL replica, updates the recovery-region application to use the promoted database endpoint, verifies migrations/configuration and application readiness, and then enables or allows global load-balancer traffic to the recovery region.
- Failover ordering and health gates prevent traffic from reaching an application that cannot use the promoted database. Connection draining and client retry behavior are tested.
- The complete load-balancer, database promotion, endpoint/configuration, application readiness, and CDC recovery path is exercised annually.

## 6. Transactional database and analytics

- Cloud SQL for PostgreSQL runs in europe-west2 with HA enabled, automated backups, and point-in-time recovery. The HA standby is not used as a read endpoint.
- Dashboards use a separately provisioned and sized Cloud SQL read replica (or another explicitly supported managed reporting path). Its lag, capacity, connection behavior, and failure behavior are monitored; reporting cannot overload the primary.
- A continuously maintained cross-region read replica in europe-west1 supports regional recovery. Replication is asynchronous. Replica lag and replay position are monitored, with escalation when the measured lag threatens the 5-minute RPO.
- The promotion runbook and recovery-region application configuration are tested to demonstrate the 15-minute RTO and 5-minute RPO. The RPO is an operational target, not an unconditional guarantee.
- Backup restore time is size-dependent. A tested restore objective, based on the actual database size and backup/PITR method, is recorded and included in recovery rehearsals; no size-independent five-minute claim is made.

## 7. Change data capture and BigQuery

- Datastream uses a supported Cloud SQL PostgreSQL logical-decoding configuration and writes committed changes to BigQuery, with a target freshness of approximately five minutes.
- CDC freshness and replication lag alert at three minutes. Logical replication slot retention, WAL volume, primary disk usage, and Datastream health are monitored with explicit thresholds and escalation.
- If Datastream is unavailable or lagging, bounded retention/backpressure procedures prevent WAL or slot growth from exhausting primary storage. CDC is repaired or re-seeded from a documented recovery point when necessary.
- BigQuery freshness/staleness settings and merge/idempotency behavior are documented and tested. Duplicate delivery does not create duplicate rows.

## 8. Security

- Workloads use Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only pipeline-built images.
- Personal-data columns use BigQuery policy tags, and datasets use customer-managed encryption keys.

## 9. Observability and operations

- SLIs are load-balancer request success rate and latency. Burn-rate alerts cover one-hour and six-hour windows.
- Dashboards include regional traffic and health, per-zone node/pod capacity, autoscaler state, Cloud SQL primary/replica health and lag, cross-region replay position, backup/PITR readiness, Datastream freshness, slot/WAL retention, and primary disk usage.
- Runbooks cover zone failure, regional recovery, replica promotion, endpoint switching, CDC interruption/re-seeding, and backup restore.

## 10. Validation

- A zone-failure game day occurs quarterly.
- A full regional recovery rehearsal occurs annually and records measured RTO, RPO, replica lag, application readiness time, load-balancer failover time, and CDC recovery results.
- Production build approval requires load testing at peak traffic, upgrade/drain testing with the selected PDB, IP-range and autoscaler validation, Datastream failure testing, and evidence that the dependency-aware availability objective is achievable.