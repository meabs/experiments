# Highly available GKE platform with a Cloud SQL analytics feed: design v2

## 1. Targets

- Customer-facing stateless web/API service, with 99.95% end-to-end monthly availability target.
- Peak traffic is approximately 5,000 requests/second.
- Survive loss of one zone without operator intervention.
- Regional recovery in a second region with a rehearsed 15-minute RTO and demonstrated 5-minute RPO.
- Every committed change should reach BigQuery within approximately five minutes without endangering the transactional primary.
- The platform uses managed GKE, Cloud SQL, global load balancing, Datastream, and BigQuery. The availability objective is an end-to-end SLO with an explicit dependency budget; individual managed-service SLAs are not multiplied or treated as proving the platform target.

## 2. Cluster and node topology

- One regional GKE Standard cluster in `europe-west2`, with control plane replication across three zones and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling.
- VPC-native private nodes with authorized control-plane networks.
- Size the pod secondary range from the maximum node count, GKE per-node allocation, and surge/autoscaling headroom. The original `/22` is insufficient; use a validated range such as `/18` or `/20` based on the final node and `maxPodsPerNode` calculation, with expansion planned.
- Internet egress uses Cloud NAT on a regional Cloud Router.
- Use the GKE Regular release channel for production. Maintain a Sunday 02:00–06:00 local-time maintenance window and validate upgrades in a pre-production environment.

## 3. Capacity

- Each API pod serves approximately 800 requests/second; deploy at least six replicas, with load and failure testing validating the 5,000-request/second peak.
- Size each zone for approximately 60% utilization at peak. After one-zone loss, the remaining zones must serve the load within the tested capacity target while autoscaling adds nodes.
- Validate capacity with one-zone failure, node drains, rolling upgrades, and regional recovery tests.

## 4. Workload placement and disruption

- Stateless tiers use six or more replicas with topology spread constraints across zones (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Use required hostname anti-affinity where node separation is a hard requirement; otherwise document the tested scheduling assumption.
- Use a drainable PDB, initially `minAvailable: 5` for six replicas (or an equivalent tested `maxUnavailable`), rather than `6/6`. Confirm that the resulting minimum capacity meets the availability SLO.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, and upgrade behavior is tested with the PDB and capacity limits.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with healthy backends in each region. Health checks use a meaningful application health endpoint, and connection draining is 60 seconds.
- Regional failover uses the load balancer's tested health-based backend failover/traffic-steering policy, not a 3,600-second DNS cutover. Any DNS used for service discovery has a documented TTL and resolver-cache limitation.
- The recovery runbook covers traffic switching, application configuration and secrets, Cloud SQL replica promotion, connection cutover, CDC/Datastream behavior, validation, and rollback. Annual rehearsals must demonstrate the 15-minute RTO.

## 6. Database

- Cloud SQL for PostgreSQL uses regional HA, with automatic failover between zones. Its HA standby is not used for reporting.
- Dashboards use a separate supported Cloud SQL read replica or reporting replica, with lag, capacity, and failure behavior monitored. Reporting must not overload the transactional primary.
- A cross-region read replica in `europe-west1` is the regional-recovery target. Monitor replication lag and WAL/replication health; the observed lag must support the 5-minute RPO.
- Promotion and application connection cutover are documented and tested.
- Point-in-time recovery and automated backups remain enabled. Restore time is size-dependent: define a measured restore objective for the actual database size and verify it in recovery exercises; do not assume a universal five-minute restore.

## 7. Change data capture to BigQuery

- Datastream reads changes from the Cloud SQL primary using a validated logical-decoding configuration and writes them to BigQuery.
- Monitor Datastream lag, replication-slot/WAL growth, primary CPU/I/O, and failures. Alert at three minutes; target freshness is five minutes.
- CDC configuration and load testing must demonstrate that logical decoding does not threaten primary capacity.
- BigQuery staleness and cost controls must not violate the five-minute freshness objective. Events are idempotently applied, for example by merge on the primary key.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default.
- Binary Authorization admits only pipeline-built images.
- BigQuery personal-data columns use policy tags, and datasets use customer-managed encryption keys.

## 9. Observability and SLOs

- Measure request success rate and latency at the load balancer and define an explicit end-to-end availability budget for load balancing, GKE, Cloud SQL, dependencies, and planned maintenance.
- Alert on one-hour and six-hour error-budget burn rates.
- Dashboard zonal capacity, autoscaler state, PDB/upgrade status, Cloud SQL HA and read-replica lag, cross-region replication lag, Datastream freshness and slot/WAL growth, and BigQuery freshness.
- Alert when recovery prerequisites or the five-minute RPO evidence are not met.

## 10. Testing and acceptance

- Quarterly zone-failure game days validate automatic zonal survival, scheduling, capacity, and database behavior.
- Annual regional recovery rehearsals validate the 15-minute RTO, five-minute demonstrated RPO, traffic and connection cutover, CDC continuity, and rollback.
- Before build sign-off, perform load, node-drain, upgrade, read-replica, CDC, and backup-restore tests and record measured results in the runbooks.