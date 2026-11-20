# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets

- End-to-end service availability target: 99.95% per month, with an approximately 22-minute monthly error budget. This is an end-to-end SLO, not the result of multiplying independent component availabilities.
- Survive loss of one zone without operator action.
- Survive loss of the primary region through a documented and rehearsed recovery in europe-west1, with a tested end-to-end RTO of 15 minutes and a tested RPO objective of 5 minutes.
- Peak traffic is approximately 5,000 requests/second. The team consists of eight engineers using managed services wherever practical.

## 2. Cluster and node topology

- The primary is a regional GKE Standard cluster in europe-west2, with the control plane replicated across three zones and node pools distributed across all three zones.
- A continuously provisioned GKE Standard recovery cluster/backend exists in europe-west1. Its configuration, images, capacity, autoscaling, networking, policies, and load-balancer integration are continuously validated so it can serve 5,000 requests/second during regional recovery.
- Separate system and application node pools use cluster autoscaling.
- The pod secondary range is sized from the node and pod-capacity plan, accounting for GKE allocation behavior, maximum nodes, and 110 pods per node, with documented growth headroom. It must be validated before production.
- Both clusters are VPC-native with private nodes. Control-plane access is restricted to authorized networks. Internet egress uses Cloud NAT through a regional Cloud Router.
- Use the Regular GKE release channel unless a tested feature requirement justifies another channel. Validate upgrades in pre-production and perform them during a defined maintenance window with rollback and disruption procedures.

## 3. Capacity

- Each API pod serves approximately 800 requests/second under the production workload. Plan at least 11 replicas at peak, or demonstrate an equivalent validated per-pod capacity, so the worst-case loss of one zone still leaves capacity for 5,000 requests/second. Load-test actual application and resource limits.
- Replica placement, node reservations, and autoscaling must be calculated explicitly for the worst zone loss. For example, with 11 replicas distributed 4/4/3, loss of a four-replica zone leaves seven replicas, or approximately 5,600 requests/second at the stated rate.
- Both regions reserve sufficient node and pod capacity for the recovery/failure mode and do not rely on nodes that cannot be provisioned.
- Autoscaler behavior, pod startup time, load-balancer convergence, and secondary-region readiness are tested during zone-failure and regional-recovery exercises.

## 4. Workload placement and disruption

- Stateless tiers use at least 11 replicas, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Required hostname anti-affinity is used where one-replica-per-node separation is required; capacity planning ensures it does not prevent recovery or upgrades.
- Each tier has a workload-specific PodDisruptionBudget. A starting point is `minAvailable: 10` for 11 replicas, subject to load testing and confirmation that voluntary drains remain possible. PDBs do not protect against involuntary failures.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to sufficient reserved capacity. Upgrade behavior is tested before production rollout.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. The europe-west1 backend is the continuously provisioned and capacity-validated recovery cluster, not an unprovisioned placeholder.
- Health checks use a narrowly scoped application health endpoint that verifies the service can serve traffic without making an unsafe dependency check.
- The recovery runbook is: validate the europe-west1 cluster, nodes, workloads, configuration, and capacity; promote the Cloud SQL cross-region replica; fence the old primary; verify the new database is writable; update application connections and validate application readiness; verify CDC behavior; then enable global load-balancer traffic failover. Traffic is not routed before database and application checks pass.
- Regional failover uses the load balancer’s health-based backend failover and is tested end-to-end to meet the 15-minute RTO. DNS is not the failover control path. Any DNS records used for access have TTLs and cache behavior documented separately.
- Connection draining is 60 seconds, and deployment/failover tests verify that existing connections and retries behave safely.

## 6. Database

- Cloud SQL for PostgreSQL in europe-west2 uses HA with a primary and standby in separate zones and automatic regional failover.
- Analytics dashboards use a supported, separate read replica, not the HA standby. Replica capacity, lag, read-only behavior, and failure handling are monitored and documented.
- A cross-region read replica in europe-west1 is the regional-recovery target. Promotion is performed by a documented runbook including application connection changes, fencing the old primary, validation, and reconciliation of lost transactions.
- Cross-region replication is asynchronous, so the five-minute RPO is an objective, not a guarantee. Replica lag is continuously measured and alerted on; recovery is rehearsed with representative data and failure conditions.
- Backups and point-in-time recovery are enabled. Corruption recovery has a tested, database-size-dependent restore RTO; the design makes no unconditional five-minute restore claim. Restore and validation procedures are rehearsed.

## 7. Change data capture to BigQuery

- Datastream is configured only after validating that the selected Cloud SQL PostgreSQL logical-decoding configuration is supported.
- Datastream reads changes from the primary and writes to BigQuery. The target freshness is five minutes, with alerts at three minutes.
- Replication-slot lag, WAL retention, primary storage, CPU, and I/O are monitored. A runbook pauses or safely remediates CDC before slot retention can endanger the primary.
- BigQuery staleness is limited to 15 minutes for cost control, while the committed-change freshness objective remains approximately five minutes.
- CDC application is idempotent, for example by merging on primary key with appropriate delete handling. Duplicate-event and restart behavior, including Cloud SQL promotion, is tested.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny inter-namespace traffic by default. Binary Authorization admits only images built and signed by the approved pipeline.
- Personal-data columns use BigQuery policy tags, and datasets use customer-managed encryption keys.

## 9. Observability

- SLIs are request success rate and latency measured at the load balancer, with one-hour and six-hour error-budget burn-rate alerts.
- Dashboards and alerts cover regional backend health, secondary-cluster readiness and capacity, failover state, replica lag, CDC freshness and slot/WAL pressure, database health, node capacity per zone, pod scheduling failures, and autoscaler state.
- Alerts have documented owners, escalation paths, and runbooks.

## 10. Testing and operations

- Conduct a quarterly zone-failure game day covering traffic, scheduling, autoscaling, database behavior, and CDC.
- Conduct at least an annual full regional recovery rehearsal. Demonstrate the 15-minute end-to-end RTO and five-minute RPO objective using representative workload and database sizes, including secondary-cluster readiness, Cloud SQL promotion, writable/readiness checks, CDC behavior, and load-balancer failover.
- Test GKE upgrades, node drains, PDB behavior, load-balancer failover, Cloud SQL promotion, backup restoration, CDC restart, and corruption recovery before production rollout and after material architecture changes.
- Each exercise produces a written report with measured results, identified gaps, and tracked remediation.