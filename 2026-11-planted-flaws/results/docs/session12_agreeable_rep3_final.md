# Highly available GKE platform with a Cloud SQL analytics feed: design v2

## 1. Targets

- Customer-facing stateless web/API service with a 99.95% monthly end-to-end availability SLO and an explicit error budget allocated across the load balancer, GKE, application, and Cloud SQL.
- Peak traffic is approximately 5,000 requests/second, with tested capacity and failure headroom.
- Survive loss of one zone without operator intervention.
- Survive loss of the primary region through a documented and rehearsed recovery in a second region, with a 15-minute RTO and 5-minute RPO.
- The team is eight engineers operating managed services.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with a regional control plane and node pools distributed across all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled.
- The VPC-native pod secondary range is sized from the actual GKE alias-IP allocation formula, maximum node count, maximum pods per node, and growth plan. It is at least /20 for the current plan and will be expanded if capacity validation requires it.
- Nodes are private. Control-plane access is restricted to authorized networks. Internet egress uses Cloud NAT through a regional Cloud Router.
- Use the Regular GKE release channel (or Stable if it meets required features), with upgrades tested before production rollout and a weekly maintenance window on Sunday 02:00–06:00 local time.

## 3. Capacity

- The API deployment starts with at least seven replicas; six replicas at 800 requests/second would not meet the 5,000-request/second peak. Load tests establish actual per-pod capacity, scaling thresholds, and additional headroom.
- Capacity is distributed across zones. Each zone is sized and autoscaled so that the remaining two zones can serve peak traffic after loss of one zone, subject to validated resource limits and scale-up time.
- Capacity tests include a zone failure, node disruption, rolling upgrade, and representative database/CDC load.

## 4. Workload placement and disruption

- Stateless tiers use at least seven replicas, topology spread constraints across zones with maxSkew 1 and `whenUnsatisfiable: DoNotSchedule`, and hostname anti-affinity.
- PodDisruptionBudgets permit controlled maintenance while preserving service capacity, initially using `minAvailable: 6` for a seven-replica deployment. The value is validated against upgrade behavior and capacity tests.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to available quota and capacity.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use a sufficiently independent application health endpoint, and connection draining is 60 seconds.
- Regional failover uses health-checked global load-balancer backend failover, not a 3,600-second DNS TTL. Any DNS used for bootstrap or emergency procedures has a low, documented TTL, with resolver and client-cache limitations tested.
- The regional recovery runbook covers deploying the application and configuration, restoring or accessing secrets, enabling the standby region, load-balancer routing and health checks, promoting the Cloud SQL cross-region replica, updating connection configuration, validation, and communication. Recovery is rehearsed at least annually.

## 6. Database

- Cloud SQL for PostgreSQL uses regional high availability: a primary and an automatic-failover standby in separate zones. The HA standby is not used for reads.
- Dashboards use a separately provisioned supported read replica, or BigQuery where appropriate. Its capacity, lag, failover behavior, and reporting workload are monitored.
- A cross-region read replica in europe-west1 is monitored for replication lag and is the regional recovery target. The measured lag and promotion procedure must substantiate the 5-minute RPO.
- Automated backups and point-in-time recovery are enabled. Restore objectives are size-dependent, measured in regular restore tests, and documented; no fixed restore time is assumed regardless of database size.
- Recovery procedures include validation of data freshness, application connectivity, and write safety after promotion.

## 7. Change data capture to BigQuery

- Datastream reads PostgreSQL changes through supported logical-decoding configuration and writes them to BigQuery without allowing replication slots or retained WAL to exhaust primary storage.
- The target is source-commit-to-BigQuery freshness of approximately five minutes. Monitoring measures source commit timestamps through destination application, not merely connector health.
- Alerts fire before the objective is breached, including at three minutes, and also cover connector failure, replication-slot/WAL retention, primary storage, and backpressure.
- The recovery plan covers connector restart/repositioning and duplicate or replayed events. Idempotent merges on the primary key prevent duplicate rows.
- BigQuery staleness and cost controls are retained, with a documented maximum acceptable staleness of 15 minutes for reporting.

## 8. Security

- Workloads use Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only images built by the approved pipeline.
- Personal-data columns use BigQuery policy tags, and datasets use customer-managed encryption keys.
- Regional recovery includes replicated or reproducibly provisioned IAM, secrets, keys, and configuration, with access tested during rehearsals.

## 9. Observability

- SLIs are load-balancer request success rate and latency, with burn-rate alerts over one-hour and six-hour windows.
- Dashboards and alerts cover regional backend health, failover state, application capacity, node and pod capacity by zone, autoscaler state, Cloud SQL HA and replica lag, cross-region lag, backup status, Datastream source-to-destination freshness, replication-slot/WAL retention, and BigQuery freshness.
- End-to-end SLO and dependency error budgets are reviewed together; individual 99.95% dependency assumptions are not treated as guaranteeing a 99.95% composed platform.

## 10. Testing and acceptance

- Before production, test peak load with headroom, loss of a zone, node-pool upgrades, Cloud SQL failover, read-replica behavior, CDC lag/recovery, and cross-region promotion.
- Run a zone-failure game day quarterly and a full regional recovery rehearsal annually, each with a written report and tracked remediation.
- Build approval requires measured capacity, restore, failover, replica-lag, and CDC-freshness results demonstrating the stated SLO, RTO, and RPO objectives.