# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets

- End-to-end platform availability SLO: 99.95% per month, allowing approximately 22 minutes of unavailability. This is the platform error budget.
- The SLO is measured at the global load balancer for valid customer requests. Availability of GKE, Cloud SQL, networking, and other dependencies is treated as a dependency budget; their individual 99.95% targets do not mathematically compose to a 99.95% end-to-end result.
- The platform must survive loss of one zone without operator intervention.
- Loss of the primary region must be recoverable in a second region through a documented and rehearsed procedure, with an RTO of 15 minutes and an RPO of 5 minutes.
- Peak traffic is approximately 5,000 requests per second. The team consists of eight engineers using managed services where practical.

## 2. Cluster and node topology

- One regional GKE Standard cluster in `europe-west2`, with the control plane replicated across the region's three zones and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled.
- The pod secondary range is sized for the maximum node count, surge capacity, and growth. It is substantially larger than `/22`—for example, at least `/18` after validating the selected per-node allocation and maximum node count—and expansion procedures are documented and tested.
- The cluster is VPC-native with private nodes. Access to the control-plane endpoint is limited to authorised networks.
- Internet egress uses Cloud NAT configured for regional high availability, with appropriate capacity and monitoring, rather than relying on a single manually managed gateway.
- Use the GKE Regular release channel (or Stable if all required features are supported), following compatibility testing in a non-production environment. A weekly maintenance window runs on Sunday from 02:00 to 06:00 local time. Upgrades use a documented validation, surge, rollback, and communication procedure.

## 3. Capacity

- Each API pod serves approximately 800 requests per second under the approved workload and latency test. Deploy at least eight replicas, providing approximately 6,400 requests per second of nominal capacity and headroom above the 5,000 requests-per-second peak.
- Capacity tests validate CPU, memory, connection limits, load-balancer behavior, and autoscaler response.
- Each zone's node pool is sized to run at approximately 60% utilisation at peak traffic. After loss of one zone, the remaining zones and autoscaler must provide the required capacity without exceeding the tested utilisation and latency limits.
- Capacity planning includes system pods, rolling-upgrade surge nodes, one-zone loss, and regional recovery.

## 4. Workload placement and disruption

- Stateless tiers run at least eight replicas, distributed across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Required hostname anti-affinity is used where the availability requirement depends on replicas not sharing a node. Scheduling tests verify placement with the available node count and after a zone loss.
- Each tier has a PodDisruptionBudget that permits controlled maintenance while preserving the availability objective; for eight replicas, `minAvailable: 7` is the starting value and is validated against upgrade behavior. The budget must not make routine node drains impossible.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to capacity testing. Upgrade procedures monitor evictions, scheduling, application health, and error-budget consumption.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use a narrowly scoped application readiness endpoint that verifies the dependencies required to serve traffic.
- Regional failover uses the load balancer's health-based backend failover, not a 3,600-second DNS cutover. Backend failover behavior, client connection behavior, and recovery timing are tested.
- The regional recovery runbook first fences the failed or isolated region and prevents split-brain writes. It then promotes the Cloud SQL cross-region replica, restores and verifies application configuration and secrets, enables the second-region workload, validates data and health checks, and directs traffic to the recovered region. Application writes remain disabled until fencing, promotion, configuration recovery, and routing convergence are verified.
- Any DNS used for auxiliary endpoints has a bounded TTL compatible with the recovery objective, and resolver/client caching limitations are documented and tested.
- Connection draining and retry behavior are configured and tested; the normal connection-draining period is 60 seconds unless measurements require otherwise.

## 6. Database

- The transactional database is Cloud SQL for PostgreSQL in `europe-west2` with high availability enabled: a primary in one zone and a standby in another, with automatic intra-region failover.
- The HA standby is not used as a readable analytics endpoint.
- Dashboards use a separate supported read replica or reporting replica. Its expected lag, capacity, failure behavior, and fallback behavior are documented and monitored. Reporting load must not endanger the primary.
- Automated backups and point-in-time recovery are enabled.
- A cross-region asynchronous read replica in `europe-west1` is the target for regional recovery. Replication lag is monitored with an alert threshold below the five-minute RPO, and the measured worst-case lag under representative load is recorded.
- Promotion, application cutover, write fencing, and replication re-establishment are documented and rehearsed. The five-minute RPO is accepted only after load and failure testing demonstrates it.
- Backup restore time is not assumed to be five minutes or independent of database size. Restore RTO is measured in a representative environment, documented, and included in the recovery rehearsal. If it cannot meet the regional recovery objective, the cross-region replica is the primary recovery mechanism.

## 7. Change data capture to BigQuery

- Datastream reads changes from the Cloud SQL primary through supported logical decoding and writes them to BigQuery. Configuration and load testing verify that CDC does not materially endanger primary-database latency or capacity.
- The committed-change freshness target is five minutes, with an alert at three minutes. Monitor the logical replication slot, WAL retention, source impact, stream health, and destination errors.
- A documented backpressure and recovery procedure protects the primary when Datastream or its replication slot falls behind, including thresholds for intervention, WAL-retention controls, and resumption or reinitialisation steps. The procedure is tested under representative load and failure conditions.
- During regional recovery, the runbook identifies the active CDC source, fences the old source as required, and prevents gaps or duplicate streams. Recovery and resumption procedures are tested.
- BigQuery freshness is displayed on dashboards and is not accepted as meeting the committed-change requirement unless it is within five minutes. Tested behavior during Datastream lag or outage, including protection and backpressure actions, is documented.
- Change events are applied idempotently using a primary-key merge and appropriate event ordering/version handling, so retries do not create duplicate rows.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default.
- Binary Authorization admits only images built and signed by the approved pipeline.
- Columns containing personal data are covered by policy tags in BigQuery, and datasets use customer-managed encryption keys.

## 9. Observability

- Service level indicators are request success rate and latency measured at the load balancer.
- Alerting covers one-hour and six-hour error-budget burn, zonal capacity, scheduling failures, node and NAT capacity, load-balancer failover, Cloud SQL health, replica lag, backup/restore status, Datastream freshness and replication-slot retention, and BigQuery freshness.
- Dashboards show regional and zonal capacity, autoscaler state, pod placement, database replication state, CDC health, and current recovery readiness.
- Alerts have documented owners and escalation procedures.

## 10. Testing and operational readiness

- A zone-failure game day is conducted at least quarterly.
- A full regional recovery rehearsal is conducted at least annually, including old-region fencing, database promotion, application cutover, configuration and secret recovery, load-balancer failover, CDC handling, validation of the measured RTO/RPO, and restoration of normal operations.
- Upgrade, node-drain, autoscaling, capacity, backup-restore, read-replica, and Datastream failure scenarios are tested before production launch and after material architecture changes.
- Each exercise produces a written report with measured results, deviations from the objectives, corrective actions, and an owner and due date for each action.