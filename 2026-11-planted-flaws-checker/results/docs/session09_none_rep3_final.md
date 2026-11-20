# Highly available GKE platform with a Cloud SQL analytics feed: design v4

## 1. Targets and availability model

- The platform target is 99.95% monthly end-to-end availability for successful customer requests, measured at the global load balancer (approximately 22 minutes of monthly unavailability).
- This is a platform SLO, not an independent 99.95% target for every dependency. GKE, Cloud SQL, load balancing, networking, and deployment processes are dependency risks whose measured behavior is reviewed against the end-to-end error budget.
- The platform must survive loss of one zone without operator action.
- Loss of the whole region requires a documented and rehearsed recovery in europe-west1, with RTO 15 minutes and RPO 5 minutes. These objectives depend on measured database/CDC lag and successful recovery execution.
- Peak traffic is approximately 5,000 requests per second. Eight engineers operate the managed services.

## 2. Cluster and node topology

- One regional GKE Standard cluster is deployed in europe-west2, with a control plane replicated across three zones and node pools in all zones.
- A warm-standby GKE cluster and supporting node capacity are maintained in europe-west1. Images, manifests, configuration, secrets references, policies, and infrastructure changes are replicated through the approved deployment pipeline. Standby capacity and readiness are tested so the second region can serve traffic during recovery.
- Separate system and application node pools use cluster autoscaling.
- The pod secondary range is sized from maximum pods per node, maximum autoscaled nodes, upgrade surge, and growth reserve. It accommodates GKE’s per-node secondary-range allocation, rather than assuming one address per running pod. For example, 30 nodes each requiring a /24 pod block require at least /19, subject to final tested limits, with expansion planned.
- The cluster uses private VPC-native nodes. Control-plane access is limited to authorised networks. Internet egress uses Cloud NAT through a regional Cloud Router.
- The Regular or Stable release channel is selected after compatibility testing; Rapid is not the production default. A tested weekly maintenance window runs Sunday 02:00–06:00 local time.

## 3. Capacity

- Each API pod serves approximately 800 requests per second under representative load. Eight replicas provide approximately 6,400 requests per second before additional autoscaled capacity, exceeding the 5,000-request-per-second peak.
- Capacity is validated by load testing during rollout, autoscaling, and single-zone-loss scenarios.
- Each zone’s node pool is sized for approximately 60% utilisation at peak traffic. Following loss of one zone, the remaining zones carry traffic while the autoscaler adds capacity. Node pools and pod ranges include headroom for this response and surge upgrades.
- The warm-standby region has sufficient tested application and node capacity for documented recovery load, or a documented scale-up step that remains within the 15-minute RTO.

## 4. Workload placement and disruption

- Stateless tiers run eight replicas, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Preferred hostname anti-affinity reduces co-location; capacity and topology constraints, rather than an absolute anti-affinity guarantee, provide availability.
- Each tier has a PodDisruptionBudget initially set to `minAvailable: 5`. This permits planned maintenance while preserving serving capacity; the setting is validated during zonal-loss and upgrade tests.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to sufficient range and node capacity.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use `/healthz`; connection draining is 60 seconds.
- The second-region backend is attached to the warm-standby GKE cluster and is continuously validated for deployment, configuration, capacity, and readiness.
- Regional failover uses the load balancer’s health-based backend failover policy, tested during recovery rehearsals. DNS is not the primary failover mechanism, so a 3,600-second DNS TTL does not determine the regional RTO.
- Failover validation confirms standby application capacity, database promotion, and write fencing before customer writes are enabled.

## 6. Database

- Cloud SQL for PostgreSQL runs in europe-west2 with HA enabled: a primary and standby in separate zones with automatic regional failover. The HA standby is not a reporting endpoint.
- Automated backups and point-in-time recovery are enabled.
- Analytics uses a separate supported Cloud SQL read replica, or equivalent supported reporting path, sized for reporting workload. Lag, health, and failure behavior are monitored; dashboards fall back or fail safely if it is unavailable.
- A cross-region read replica in europe-west1 is the regional-recovery target. Replication is asynchronous. Measured lag must remain within the five-minute RPO, with alerts and an escalation/runbook when it does not.
- Regional recovery uses documented promotion and write fencing to prevent split-brain and prevent the old primary accepting writes. It includes application reconfiguration and promotion validation.
- Restore time is not assumed to be five minutes or independent of database size. Restore and point-in-time recovery objectives are measured with production-scale data, documented as tested values, and included in the recovery plan. Restore validation includes integrity checks and application connectivity.

## 7. Change data capture to BigQuery

- Datastream reads changes from the Cloud SQL primary through logical decoding and writes them to BigQuery. Dashboard queries and extraction load do not use the primary.
- The required committed-change freshness SLO is five minutes. A 15-minute freshness result is an SLO breach, not a silently permitted alternative. Alerts cover source capture lag, logical replication-slot and retained-storage growth, Datastream lag, and BigQuery apply lag; an alert fires at three minutes.
- Source impact is bounded by tested thresholds for database CPU/latency, slot lag, and retained storage. When a threshold is exceeded, Datastream is throttled or paused according to the runbook, the primary is protected, and operators reconcile the resulting gap. The backpressure policy and recovery behavior are tested at production scale.
- CDC behavior during promotion, regional recovery, and restore is documented. Replication is paused or re-established safely, and gaps are reconciled.
- CDC acceptance tests cover event ordering, inserts, updates, deletes, retries, duplicate delivery, schema changes, failover gaps, replay, and end-to-end reconciliation. Schema changes use a documented compatibility and deployment procedure; incompatible changes block or quarantine affected events rather than corrupting the target.
- Change events are applied idempotently using a merge on the primary key, with explicit event ordering, deduplication, delete, and replay policies. Duplicate or retried events do not create duplicate rows.
- The five-minute freshness SLO, source-protection thresholds, and cost impact are validated in testing.

## 8. Security

- Workloads reach Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny inter-namespace traffic by default, and Binary Authorization admits only images built by the approved pipeline.
- Personal-data columns use BigQuery policy tags, and datasets use customer-managed encryption keys.

## 9. Observability

- SLIs are request success rate and latency measured at the load balancer. Alerts cover one-hour and six-hour error-budget burn rates.
- Dashboards show database replica and CDC lag, source retained-storage/slot risk, BigQuery freshness and apply lag, node capacity per zone, autoscaler state, and regional failover readiness.
- Recovery and promotion checks produce auditable events and alerts when measured RPO or RTO cannot be met.

## 10. Testing and operations

- A zone-failure game day runs quarterly and verifies automatic continuity, autoscaler capacity, topology placement, and database behavior.
- A full regional recovery rehearsal runs annually, including load-balancer failover, warm-standby readiness and capacity, database promotion and fencing, connection reconfiguration, CDC pause/restart and reconciliation, and restoration of normal operations. Each exercise has a written report.
- Upgrade, capacity, restore, failover, and CDC replay tests use production-scale assumptions. CDC tests explicitly verify ordering, deletes, schema changes, bounded source load/backpressure, retries, failover gaps, duplicate handling, and reconciliation.
- Measured results update the SLO/error-budget, RTO, RPO, capacity, range-sizing, and CDC runbook documents.