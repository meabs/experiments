# Highly available GKE platform with a Cloud SQL analytics feed: design v2

## 1. Targets and acceptance criteria

- The customer-facing service has a 99.95% monthly end-to-end availability SLO, measured at the global load balancer. Dependencies are not each assumed to provide 99.95%; their availability and failure modes are included in the end-to-end error budget.
- The platform operates primarily in europe-west2 and is designed to continue serving after loss of one zone without operator intervention.
- Loss of the primary region has a documented and rehearsed recovery in europe-west1. The achievable RTO is 15 minutes and the achievable RPO is no more than five minutes, subject to measured cross-region replication lag.
- Peak traffic is approximately 5,000 requests per second. Capacity and failover claims must be demonstrated by load and failure tests before production launch.
- The team consists of eight engineers and uses managed services wherever practical.

## 2. Cluster and node topology

- One regional GKE Standard cluster is deployed in europe-west2, with nodes in all three zones.
- Separate system and application node pools use cluster autoscaling. The application pool has sufficient tested spare capacity to tolerate loss of one zone and continue serving at the required SLO.
- The pod secondary range is sized from the selected `maxPodsPerNode`, maximum node count, GKE secondary-range allocation behavior, and growth headroom. The original /22 assumption is rejected; the final range must be confirmed from the actual node-pool limits before provisioning.
- The cluster is VPC-native with private nodes. Control-plane access is restricted to authorized networks. Internet egress uses Cloud NAT with appropriately sized NAT IP capacity and monitoring.
- Use the Regular or Stable GKE release channel, selected after checking required versions and support policy. A tested weekly maintenance window is configured; upgrades are validated in a non-production environment first.

## 3. Capacity

- Initial capacity is based on load-test measurements rather than the estimate of 800 requests per second per pod. At least six API replicas are deployed initially, with autoscaling thresholds and limits established from testing.
- Capacity tests cover peak traffic, rolling upgrades, loss of each zone, node-pool autoscaling, and regional failover.
- The recovery region has provisioned cluster, node, load-balancer, and database capacity sufficient for the required traffic, rather than relying on an untested scale-up during the incident.

## 4. Workload placement and disruption

- Stateless tiers run at least six replicas with required topology spread constraints across zones and, where required, across hostnames. Scheduling rules are tested rather than relying on preferred anti-affinity alone.
- PodDisruptionBudgets permit controlled voluntary disruption, for example `maxUnavailable: 1` for a six-replica tier. PDBs are not used as a substitute for spare capacity.
- Node pools use surge upgrades with settings selected from capacity tests. Upgrade and drain behavior, including PDB interaction, is tested before production.
- Readiness probes, startup probes, graceful termination, and connection draining prevent traffic from being sent to unavailable or terminating pods.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use a narrowly scoped endpoint that verifies the application can serve traffic; dependency checks are designed not to create unnecessary cascading failure.
- Regional backend failover is health based and is tested end to end. A 3,600-second DNS TTL is not used as the regional failover mechanism.
- Regional recovery runbook steps are explicit: fence or stop writes in the failed region where necessary, promote the Cloud SQL cross-region replica, update application database configuration and secrets, enable the recovery-region workloads, verify migrations and health checks, and shift traffic.
- The recovery procedure includes rollback and split-brain prevention. Its RTO and RPO are measured in rehearsals, not assumed.

## 6. Database

- Cloud SQL for PostgreSQL uses regional high availability, automated backups, and point-in-time recovery. The HA standby is failover-only and is not treated as a read endpoint.
- Analytics dashboards use a separately provisioned, supported Cloud SQL read replica or an explicitly approved BigQuery serving path. The replica has independent sizing, lag monitoring, and documented behavior during primary failover.
- A cross-region read replica in europe-west1 is used for regional recovery and is promoted by the recovery runbook. Replication lag is continuously monitored; the five-minute RPO is accepted only while measured lag remains within that limit.
- Backup/PITR restoration time is database-size dependent. The design makes no universal five-minute restore claim. Restore time, data validation time, and the resulting RTO are measured in scheduled restoration tests and reported with database size.
- Database schema changes use an online, backward-compatible migration process. A bad migration has a documented rollback or PITR procedure, including write isolation and verification before reopening traffic.

## 7. Change data capture to BigQuery

- Datastream reads Cloud SQL changes using a supported configuration and is tested for source load, logical-decoding/WAL retention, failure recovery, and backpressure.
- Monitoring alerts on replication lag, source WAL/disk growth, connector health, and BigQuery freshness. Datastream lag must not be allowed to exhaust primary database storage.
- The target freshness objective is approximately five minutes. A 15-minute maximum staleness alert/SLO threshold is not presented as meeting the five-minute requirement; the alert thresholds and escalation policy are defined separately.
- Destination writes are idempotent using documented keys and merge semantics. Duplicate and out-of-order event behavior is tested.
- After regional promotion, CDC is paused, reconfigured, or restarted according to the documented source identity and checkpoint procedure. The procedure prevents duplicate or missing changes and includes reconciliation.

## 8. Security

- Workloads use Workload Identity for GKE with one least-privilege Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default, with explicitly reviewed exceptions. Binary Authorization admits only approved pipeline-built images.
- Personal-data columns in BigQuery use policy tags and least-privilege dataset access. Customer-managed encryption keys are used where required, with rotation and recovery procedures tested.
- Secrets and regional endpoint configuration are available in the recovery region without requiring access to the failed region.

## 9. Observability and operations

- SLIs are load-balancer request success rate and latency, with separate database, dependency, CDC freshness, and regional-failover indicators.
- Alerts cover fast and slow error-budget burn, zone capacity, autoscaler state, pod scheduling failures, node upgrade health, Cloud SQL failover, replica lag, WAL/storage growth, Datastream health, and BigQuery freshness.
- Runbooks identify owners, escalation paths, and safe actions for zone failure, database failover, regional recovery, CDC interruption, and rollback.

## 10. Testing and release gates

- Before production, the team load-tests at and above 5,000 requests per second, including loss of one zone and rolling node upgrades.
- A quarterly zone-failure and upgrade game day verifies automatic service continuity.
- A regional recovery rehearsal is performed at least annually and after material architecture changes. It measures RTO, RPO, replica lag, traffic convergence, application configuration readiness, and CDC recovery.
- Backup restoration and PITR are tested on representative database sizes. Results replace estimates in the operational runbooks.
- Production approval requires evidence that the end-to-end 99.95% SLO, single-zone continuity, five-minute CDC objective, and measured regional RTO/RPO are achievable.