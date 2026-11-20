# Highly available GKE platform with a Cloud SQL analytics feed: design v2

## 1. Targets and availability

- Customer-facing stateless web/API platform for users in one continent; peak traffic is approximately 5,000 requests/second.
- End-to-end monthly availability SLO is 99.95% (approximately 22 minutes of error budget). Dependency budgets for GKE, load balancing, Cloud SQL, and supporting services are allocated explicitly; component availability is not treated as additive.
- The platform operates without intervention through loss of one zone.
- Loss of a region is handled by a documented and rehearsed recovery with a 15-minute RTO and 5-minute RPO.
- The design is sized for a team of eight engineers using managed services.

## 2. Cluster and network topology

- One regional GKE Standard cluster in europe-west2, with a replicated control plane and node pools across all three zones.
- Separate system and application node pools, both using cluster autoscaling. Each zone is provisioned with N+1 capacity headroom for zone loss, bursts, rollout surge, and autoscaler delay; post-failure operation is not dependent on emergency scaling alone.
- The VPC-native private cluster uses secondary ranges sized from the maximum autoscaled node count, maximum pods per node, surge capacity, IP-allocation overhead, and growth headroom. The former /22 is insufficient and is replaced by a capacity plan approved before build.
- Control-plane access is restricted to authorised networks. Internet egress uses Cloud NAT through a regional Cloud Router.
- Use the GKE Regular or Stable release channel (Stable where required features permit). Every upgrade is validated in a non-production environment, performed in a defined maintenance window, and has a tested rollback/mitigation procedure.

## 3. Capacity

- API capacity is measured under representative load, including headroom. Deploy at least seven API replicas initially (six replicas at 800 requests/second is only 4,800 requests/second), and revise replica/node counts from load-test results.
- Capacity is distributed across zones so that loss of one zone leaves sufficient tested capacity for peak traffic, bursts, and maintenance activity.

## 4. Workload placement and disruption

- Stateless tiers use at least seven replicas where required by capacity testing, topology spread constraints across zones, and required hostname separation when one-replica-per-node placement is a requirement. Scheduling tests verify the guarantees.
- PodDisruptionBudgets preserve a defined serving minimum while permitting voluntary drains; for six replicas, use a tested budget such as `minAvailable: 5`, rather than 6 of 6.
- Node pools use surge upgrades with `maxUnavailable: 0` where supported, and upgrade procedures verify that PDBs, topology constraints, and available capacity do not deadlock maintenance.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with healthy backends in both regions. Health checks use an application endpoint that reflects readiness for serving traffic, and connection draining is 60 seconds.
- Regional failover uses the load balancer’s health-based backend failover, not a DNS update during the 15-minute recovery window. Backend health, failover behavior, and recovered-region capacity are tested. DNS is not relied upon for rapid client cutover.
- The regional recovery runbook measures cross-region database-replica lag, promotes the replica, updates application database endpoints/credentials and write configuration, reconfigures and validates Datastream, performs reconciliation checks, and then enables/shifts traffic to the recovered region. Timing is tested against the 15-minute RTO and 5-minute RPO.

## 6. Cloud SQL

- Cloud SQL for PostgreSQL uses regional HA: a primary and automatic-failover standby in separate zones. The HA standby is not used for reads.
- Analytics dashboards use a separately provisioned supported Cloud SQL read replica (or another explicitly supported reporting architecture), sized and monitored for query load and replication lag. Its behavior during primary and regional failover is documented.
- A cross-region read replica in europe-west1 is the regional-recovery target. Its measured lag is continuously monitored against the 5-minute RPO; promotion and post-promotion validation are rehearsed.
- Automated backups and point-in-time recovery are enabled. Restore time is treated as database-size-dependent: restore, validation, integrity checks, and application cutover are measured in drills and documented rather than assumed to take five minutes.

## 7. Change data capture to BigQuery

- Datastream reads committed changes from Cloud SQL using a supported logical-decoding configuration. It is monitored for freshness, replication lag, slot/WAL retention, and primary-storage impact; alerts and runbooks address backlog and unsafe retention growth.
- The target freshness objective is approximately five minutes, with an alert at three minutes. During regional recovery, the runbook records the source position, restarts or reconfigures capture safely, and reconciles the affected interval.
- BigQuery ingestion is idempotent, with duplicate/replayed events handled by keys and merge semantics and gap detection/replay procedures documented and tested. BigQuery staleness limits are aligned with the freshness objective and business requirements.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only pipeline-built images.
- BigQuery personal-data columns use policy tags, and datasets use customer-managed encryption keys.

## 9. Observability

- SLIs are load-balancer request success rate and latency. Alerts cover one-hour and six-hour error-budget burn.
- Dashboards and alerts cover regional backend health, failover state, per-zone capacity, autoscaler state, Cloud SQL HA/replica health and lag, cross-region RPO lag, Datastream freshness and slot/WAL retention, BigQuery staleness, and recovery-runbook milestones.
- Dependency error budgets and end-to-end SLO reporting are reviewed together.

## 10. Testing and operations

- Run a zone-failure game day at least quarterly, including workload placement and capacity validation.
- Run a full regional recovery rehearsal at least annually, including database promotion, application cutover, load-balancer failover, Datastream continuity, duplicate/gap reconciliation, and measured RTO/RPO.
- Test GKE upgrades, rollback/mitigation, database restores, read-replica failover behavior, and CDC backlog recovery. Each exercise produces a written report and tracked corrective actions.