# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets

- Customer-facing stateless web/API service with a 99.95% monthly availability target (about 22 minutes of monthly error budget).
- Peak traffic is approximately 5,000 requests per second.
- Survive loss of one zone without operator intervention.
- Survive loss of the primary region through a documented and rehearsed recovery in a second region, with an RTO of 15 minutes and RPO of 5 minutes.
- Every committed change should reach BigQuery within approximately five minutes without endangering the Cloud SQL primary.
- The platform is operated by eight engineers using managed services.
- The availability SLO is measured at the load balancer from the user perspective. Dependency availability, maintenance, failover, and error budgets are explicitly included in capacity and operational planning; component availability figures are not assumed to compose directly into the platform SLO.

## 2. Cluster and node topology

- One regional GKE Standard cluster in `europe-west2`, with the control plane replicated across three zones and node pools distributed across all three zones.
- Separate system and application node pools, both with cluster autoscaling enabled.
- The cluster is VPC-native with private nodes. The pod secondary range is sized from the calculated maximum node count, pod density, autoscaler growth, and upgrade surge capacity; use `/18` initially unless capacity modelling justifies another size.
- Access to the private control-plane endpoint is limited to authorised networks. Internet egress uses Cloud NAT through a regional Cloud Router.
- Use the Regular GKE release channel for production. A weekly maintenance window runs Sunday 02:00–06:00 local time.

## 3. Capacity

- The API starts with eight replicas. Per-pod throughput assumptions and resource requests are validated by load testing; eight replicas at the measured capacity must exceed peak demand with headroom.
- Capacity is distributed across zones. Each zone is sized so that the remaining two zones can carry peak traffic after loss of one zone, while retaining scheduling, autoscaling, quota, and upgrade-surge headroom.
- Before production, load tests validate pod, node, IP-range, autoscaler, and load-balancer capacity, including zone loss, rollout, and node-pool surge scenarios.

## 4. Workload placement and disruption

- Stateless tiers run eight replicas, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Preferred hostname anti-affinity reduces co-location of replicas on one node.
- Each tier uses a drainable PodDisruptionBudget, initially `minAvailable: 7`; upgrades and disruption procedures must verify serving capacity and rollout health.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to sufficient spare capacity.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with backends in both regions.
- Health checks use an appropriate application health endpoint that verifies serving readiness without making unsafe dependency checks.
- Configure and test health-based regional failover so traffic is directed to the recovery region when the primary region is unavailable. Do not rely on a 3,600-second DNS TTL for failover.
- Connection draining is 60 seconds. Regional failover behavior, client caching, capacity, and restoration of normal routing are validated in recovery rehearsals.
- The recovery runbook explicitly sequences: fence writes and mark the failed region unready; validate cross-region replica lag against the 5-minute RPO; promote the replica; redirect application connections and configuration; direct traffic through the global load balancer; then validate application readiness and writes. Communications and return to normal routing are included.

## 6. Database

- Cloud SQL for PostgreSQL runs in `europe-west2` with high availability enabled, automatic zonal failover, automated backups, and point-in-time recovery.
- The HA standby is not used for reporting. Dashboards use a dedicated in-region read replica, with replica lag and failure behavior monitored; dashboards fall back safely if it is unavailable.
- A cross-region read replica in `europe-west1` is the disaster-recovery target. Its measured replication lag must support the five-minute RPO. The recovery runbook promotes it and points the application at it.
- Backup restoration is tested regularly. Restoration time is documented as a measured, database-size-dependent objective rather than an unconditional five-minute claim. Point-in-time recovery procedures cover bad migrations and data corruption.

## 7. Change data capture to BigQuery

- Datastream reads changes from the Cloud SQL primary using logical decoding and writes them to BigQuery.
- Target freshness is approximately five minutes, with alerts at three minutes and additional monitoring for slot/transaction-log retention and source impact.
- CDC capacity, retry, and backpressure settings are bounded so replication issues cannot exhaust primary-database storage or otherwise endanger the primary.
- The BigQuery destination staleness limit is 15 minutes. Change events are applied idempotently using a merge on the primary key, with duplicate-event handling verified.
- CDC lag and recovery procedures are included in operational runbooks.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, using one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default.
- Binary Authorization admits only images built and attested by the approved pipeline.
- Personal-data columns in BigQuery use policy tags, and datasets use customer-managed encryption keys.

## 9. Observability

- SLIs are request success rate and latency measured at the load balancer.
- Alerting covers one-hour and six-hour error-budget burn, regional backend health, database failover state, read-replica lag, cross-region replica lag, CDC freshness and source impact, node capacity by zone, IP-range exhaustion, and autoscaler state.
- Dashboards show recovery-region readiness and the last successful backup/restore and recovery tests.

## 10. Testing and operations

- Conduct a zone-failure game day quarterly.
- Conduct a full regional recovery rehearsal at least annually, including the documented write-fencing, replica-lag validation and promotion, application redirection, load-balancer failover, readiness and write validation, measured RTO/RPO, and return to normal service.
- Load-test the planned peak and failure scenarios before launch.
- Record test results and update capacity limits, runbooks, and objectives when measured behavior differs from this design.