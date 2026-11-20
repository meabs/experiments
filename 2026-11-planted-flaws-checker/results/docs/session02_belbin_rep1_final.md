# Highly available GKE platform with Cloud SQL analytics feed: design v3

## 1. Targets and SLO

- Customer-facing availability SLO is 99.95% monthly, measured as successful, correctly served requests at the global load balancer (approximately 22 minutes error budget).
- Component availability targets do not compose automatically into the end-to-end SLO. Dependency availability, maintenance, and failure-mode budgets will be measured and reviewed.
- The primary region must tolerate loss of one zone without operator action.
- Regional recovery is a documented and rehearsed operation with target RTO 15 minutes and target RPO 5 minutes. RPO is demonstrated from measured asynchronous-replication lag, not assumed.
- Peak traffic is approximately 5,000 requests/second. Capacity includes zone loss, rolling upgrades, autoscaling delay, and daemonsets.

## 2. Clusters, regions, and topology

- The primary is a regional GKE Standard cluster in `europe-west2`, with control-plane replicas and node pools across three zones.
- A standby regional GKE Standard cluster is maintained in `europe-west1`, aligned with the Cloud SQL cross-region recovery target. It is provisioned and deployed through the same versioned automation and image/configuration pipeline as primary, with secrets, quotas, dependencies, and ingress configuration continuously validated.
- The standby cluster has tested capacity for the documented peak and recovery load; it is not treated as ready merely because it exists.
- Separate system and application node pools use cluster autoscaling. Maximum nodes, per-zone quotas, reservations, daemonset overhead, surge capacity, and standby capacity are explicitly sized and tested.
- VPC-native Pod secondary ranges are sized from `maxPodsPerNode`, maximum nodes, autoscaling, surge, and growth headroom. The range is substantially larger than `/22` (initially `/19`, or larger if calculations require it); final sizing is recorded in the capacity plan.
- Nodes are private. Control-plane access is restricted to authorised networks. Internet egress uses regional Cloud NAT.
- Use the Regular GKE release channel (Stable where compatible), with tested upgrades and a Sunday 02:00–06:00 local maintenance window.

## 3. Capacity and placement

- Six replicas at 800 requests/second are insufficient. Size and load-test the deployment for at least 5,000 requests/second plus documented headroom, zone loss, upgrades, and autoscaler delay. Replica counts and node limits come from those tests.
- Before build approval, demonstrate that either remaining primary zones can schedule recovery workload after any one-zone loss, including CPU, memory, pod IPs, quotas, and surge capacity. Do not target utilisation that prevents recovery.
- Stateless workloads use topology spread across zones with `maxSkew: 1` and `whenUnsatisfiable: DoNotSchedule`. Required hostname anti-affinity is used where one replica per node is required; otherwise the actual placement guarantee is documented.
- PDBs permit safe voluntary maintenance (for example, an availability floor below the full replica count such as 5 of 6). They must not block all voluntary drains. Node pools use surge upgrades with tested values and sufficient spare capacity.

## 4. Global traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with healthy backends in both `europe-west2` and the standby `europe-west1` cluster. Health checks use a meaningful application readiness endpoint.
- Health-check interval, timeout, unhealthy/healthy thresholds, backend failover policy, and connection-draining duration are explicitly configured and recorded. The selected settings are tested with injected regional and application failures.
- Failover is health-based at the load balancer, not DNS-based; DNS updates are not part of the 15-minute RTO. Tests measure detection, unhealthy-region evacuation, connection draining, client retries, traffic convergence, and end-to-end RTO.
- Recovery fences or disables writes in the failed region, promotes the database, changes application endpoints and credentials, validates the standby, and then restores normal traffic. In-flight writes and duplicate/retried requests are tested.

## 5. Database

- Cloud SQL for PostgreSQL uses regional HA with automatic in-region failover. Its HA standby is not a reporting endpoint.
- Dashboards use a separately sized supported read replica or explicitly supported analytics path. Lag, failure behavior, and protection from primary workload are monitored.
- A cross-region read replica in `europe-west1` is the regional recovery target. Promotion requires the documented fencing, lag/prerequisite checks, endpoint and credential changes, application reconnection, and validation.
- Cross-region replication is asynchronous. Rehearsals under representative load must demonstrate an achievable RPO of 5 minutes and document expected loss when lag exceeds that target.
- Backups and point-in-time recovery remain enabled. Restore and promotion durations are measured during rehearsals as size- and workload-dependent bounds; no size-independent restore claim is made.
- Regional recovery and restore drills are acceptance tests for the RTO/RPO.

## 6. CDC to BigQuery

- Datastream reads committed changes from the Cloud SQL primary using logical decoding and writes them to BigQuery without reporting queries on the primary.
- End-to-end commit-to-queryable freshness is measured and targeted at approximately five minutes, with an early warning at three minutes. BigQuery settings cannot silently permit the target to be missed.
- Logical replication slot/WAL retention, storage growth, backpressure, and Datastream failure alerts are sized and tested so lag cannot exhaust primary storage or endanger the primary.
- Merge/upsert processing is idempotent. Regional recovery validates Datastream checkpoints, slots, and destination, or follows a documented reinitialisation procedure.

## 7. Security and observability

- Workloads use Workload Identity Federation for GKE, one Google service account per tier, and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only approved-pipeline images.
- BigQuery personal-data columns use policy tags and customer-managed encryption keys.
- SLIs are load-balancer request success and latency, with one-hour and six-hour error-budget burn alerts. Dashboards include zonal/standby capacity, quotas, scheduling failures, autoscaling, database lag, Datastream lag and end-to-end freshness, WAL risk, and regional backend health.

## 8. Acceptance gates

Before build approval, written tests must demonstrate: pod-range and max-node sizing; peak, upgrade, and zone-loss capacity; standby-region readiness and capacity; configured load-balancer thresholds, draining, fencing, and measured failover RTO; Cloud SQL promotion, restore duration, and measured RPO; and CDC failure recovery with five-minute end-to-end freshness. Targets are not treated as guarantees until these tests pass or revised targets are formally approved.