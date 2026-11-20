# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets

- End-to-end customer-facing service availability SLO: 99.95% per calendar month, measured at the global load balancer for valid customer requests. This is a service-level target, not a multiplication of individual managed-service availability figures.
- The platform is designed to survive loss of one zone without operator action.
- Loss of the whole primary region has a documented and rehearsed recovery target of 15 minutes RTO and 5 minutes RPO. These are tested targets, not guarantees; actual recovery depends on measured database promotion, traffic convergence, and replication lag.
- Peak traffic is about 5,000 requests per second. The team is eight engineers on a managed-service budget.
- The end-to-end SLO, error budget, and dependency assumptions are reviewed using measured load-balancer, GKE, database, and failover results.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools in all three zones.
- A warm, separately provisioned regional GKE Standard recovery cluster is maintained in europe-west1. It has the required cluster configuration, workload manifests, approved images, secrets and configuration delivered through the approved secret-management and deployment process, IAM, quotas, load-balancer backend registration, and validated capacity for the full required workload. Its capacity and configuration are tested during regional recovery rehearsals; it is not created from scratch during an incident.
- Separate system and application node pools are used in each cluster, with cluster autoscaling enabled. Zonal quotas and spare capacity are sized for zone loss, autoscaler delay, and node upgrade surge. The recovery region has sufficient regional quota and warm capacity for the expected failover workload.
- Both clusters are VPC-native with private nodes. Pod secondary ranges are sized from the selected `maxPodsPerNode`, maximum node count, GKE alias-IP allocation (including per-node allocation overhead), recovery capacity, and upgrade headroom. The initial range is at least `/18` (subject to final capacity calculations), with expansion reserved and tested; a `/22` is not used.
- Both clusters use the Regular release channel for production. Versions are tested in a representative environment, and rollback/runbook procedures are documented.
- Access to private control-plane endpoints is limited to authorised networks.
- Internet egress uses Cloud NAT on a regional Cloud Router.
- A weekly maintenance window runs Sunday from 02:00 to 06:00 local time.

## 3. Capacity

- Each API pod can serve about 800 requests per second. Six replicas therefore exceed the 5,000 requests-per-second peak, subject to load testing and resource limits.
- Primary-region capacity is provisioned so that, after loss of any one zone, the remaining zones have explicit headroom for the full workload, autoscaler delay, and required node surge. Operation at approximately 90% utilisation is not treated as sufficient without validated load and quota tests.
- The recovery cluster is load-tested and capacity-validated for the full expected workload before it is accepted as a failover target.
- Autoscaler limits, regional quotas, scale-up alerts, and recovery-region capacity checks are documented and tested.

## 4. Workload placement and disruption

- Stateless tiers run six replicas in each active cluster, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Required hostname anti-affinity is used when one-replica-per-node placement is required; scheduling feasibility during normal operation, zone loss, and recovery-region activation is validated. Where required anti-affinity would prevent recovery, the exception and capacity trade-off are documented.
- Each tier has a PodDisruptionBudget with `minAvailable: 5` for six replicas.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to available quota and capacity.
- Readiness and health checks remove unavailable pods before traffic is sent to them.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with backends in both regions. Health checks use the application's `/healthz` endpoint, and connection draining is 60 seconds.
- The recovery-region backend is kept registered and health-checked, with traffic normally disabled or given no serving weight as appropriate. Health-based backend selection is not treated as a substitute for database promotion and application reconfiguration.
- Regional failover uses health-based load-balancer backend selection rather than relying on a 3,600-second DNS TTL. Any required DNS records use a controlled low TTL, and resolver caching limits are included in the tested convergence time.
- The recovery sequence is:
  1. Declare the regional incident and fence or stop writes from the failed region.
  2. Promote the Cloud SQL cross-region replica in europe-west1 using the recovery runbook.
  3. Update the recovery-region application configuration and database endpoint, then validate database consistency and application readiness.
  4. Validate replication and Datastream status, including the amount of data potentially lost according to measured replica lag.
  5. Enable or route traffic to healthy recovery-region backends through the global load balancer.
  6. Verify customer transactions, CDC freshness, and monitoring before declaring recovery complete.
- Promotion and traffic-convergence times are measured during rehearsals. The documented 15-minute RTO and 5-minute RPO are tested objectives, not unconditional guarantees.

## 6. Database

- The transactional database is Cloud SQL for PostgreSQL in europe-west2 with high availability enabled: a primary in one zone and a standby in another, with automatic intra-region failover. Automated backups and point-in-time recovery are enabled.
- The HA standby is not used for reads. Analytics dashboards use a separately provisioned supported Cloud SQL read replica, preferably dedicated to analytics, with its lag, capacity, failure behavior, and fallback behavior monitored and documented.
- A cross-region asynchronous read replica in europe-west1 is the regional-recovery target. Its replication lag, storage, and promotion readiness are monitored. The achievable regional RPO is lag-dependent and validated in recovery rehearsals.
- Backup restore time is database-size and storage-condition dependent; no fixed five-minute guarantee is made. Restore and point-in-time recovery procedures have measured targets, validation steps, and a documented recovery runbook.
- Recovery includes write fencing to prevent split brain and duplicate writes during or after promotion.

## 7. Change data capture to BigQuery

- Datastream reads changes from the Cloud SQL primary through supported PostgreSQL logical decoding and writes them to BigQuery without placing unsafe load on the primary.
- CDC freshness is measured end-to-end from commit to queryable BigQuery data, with a five-minute target and a replication-lag alert at three minutes.
- The logical-decoding replication slot, WAL retention, primary disk growth, Datastream backlog, and BigQuery application latency are monitored. Alerts and runbooks define throttling, restart, backlog replay, and slot remediation actions so CDC cannot exhaust primary storage.
- The BigQuery destination's staleness limit is 15 minutes for cost control, subject to the five-minute freshness objective and alerting.
- Change events are applied with a merge on the primary key; duplicate delivery is handled idempotently.
- During regional recovery, CDC status and any data gap caused by asynchronous replication are explicitly validated before recovery is complete.

## 8. Security

- Workloads reach Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default.
- Binary Authorization admits only images built by the approved pipeline.
- Columns holding personal data are covered by policy tags in BigQuery, and datasets use customer-managed encryption keys.

## 9. Observability

- Service level indicators are request success rate and latency measured at the load balancer.
- Alerts cover one-hour and six-hour error-budget burn, zonal and regional backend health, database failover state, cross-region replica lag, analytics-replica lag, Datastream freshness and backlog, logical-decoding slot/WAL retention, primary disk growth, node-pool capacity by zone and region, quota, and autoscaler state.
- Dashboards show recovery checkpoints, promotion time, traffic-convergence time, CDC freshness, and measured RPO.

## 10. Testing and operations

- A zone-failure game day is run quarterly.
- A full regional recovery rehearsal, including warm recovery-cluster capacity validation, write fencing, replica promotion, application reconfiguration, load-balancer failover, CDC validation, and rollback/follow-up actions, is run at least annually.
- Restore and point-in-time recovery tests are run against representative database sizes.
- Each exercise produces a written report with measured RTO, RPO, replica lag, traffic convergence, CDC freshness, recovery-cluster capacity behavior, and corrective actions.