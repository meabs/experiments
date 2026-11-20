# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets and availability

- Customer-facing stateless web/API service, peak 5,000 requests/second, with a 99.95% monthly end-to-end availability SLO.
- The SLO is measured at the load balancer and includes dependency and failover behavior; it is not calculated by treating three independent 99.95% dependencies as additive. Component error budgets and measured dependency availability will be reviewed before launch.
- The platform must tolerate loss of one zone without operator intervention.
- Regional recovery is rehearsed, with a target RTO of 15 minutes and RPO of 5 minutes. These targets are acceptance criteria and must be demonstrated under representative load.
- The design uses managed GKE, Cloud SQL, load balancing, and BigQuery services within the eight-engineer operational budget.

## 2. GKE topology and regional standby

- The primary platform is one regional GKE Standard cluster in europe-west2, with a replicated regional control plane and nodes distributed across all three zones.
- A prebuilt, capacity-tested standby GKE platform is maintained in europe-west1 for regional recovery. It has matching cluster configuration, namespaces, policies, images, secrets/configuration delivery, node pools, autoscaling limits, topology constraints, and deployment automation. Its capacity supports the tested production load and one-zone-loss requirements.
- The standby platform remains deployable and operationally validated through regular deployment and failover rehearsals; its load-balancer backend is registered and health-checked, but traffic is directed there only during regional recovery.
- Application, database, and CDC endpoints and credentials are configured so the standby can switch to the promoted Cloud SQL primary without rebuilding platform infrastructure. The deployment process and image/configuration synchronization are documented and tested against the 15-minute RTO. A regional rebuild is not relied upon for meeting the RTO.
- Separate system and application node pools in both regions use cluster autoscaling. Maximum node counts include one-zone-loss capacity and upgrade surge.
- The VPC-native pod secondary range is sized from the maximum simultaneously allocatable pod IPs, GKE per-node allocation, autoscaler growth, and upgrade surge, with documented headroom. It will not be a /22; the final range is validated during cluster creation and expansion is planned.
- Nodes are private. The control-plane endpoint is restricted to authorised networks. Internet egress uses Cloud NAT with regional redundancy as supported by the chosen configuration.
- Use the Regular release channel (or Stable if compatibility testing supports it), not Rapid. Maintenance windows and upgrade behavior are tested before production.

## 3. Capacity

- Capacity tests validate at least 5,000 requests/second with headroom; six 800-RPS pods are insufficient by themselves. Normal operation and one-zone-loss operation are sized with additional replicas and node capacity.
- Both primary and standby regional platforms are tested at the required load, including one-zone-loss behavior where applicable.
- Autoscaler reaction time is measured rather than assumed. A zone-loss game day verifies that existing spare capacity and scale-out preserve the service SLO during scheduling and startup delays.

## 4. Placement and disruption

- Stateless workloads use topology spread constraints across zones and required hostname anti-affinity where no two replicas may share a node. Replica counts and node capacity are validated so these constraints remain schedulable after a zone loss.
- Each tier uses a PDB that permits planned maintenance while preserving the tested serving target (initially `minAvailable: 5` for six replicas, subject to load-test results). A PDB must not be used to block all voluntary disruption.
- Node pools use surge upgrades with `maxUnavailable: 0`; drain, rollout, and rollback behavior are tested with the selected PDBs and placement constraints.

## 5. Traffic and regional recovery

- A global external Application Load Balancer has healthy backends in both regions, health checks, connection draining, and health-based regional failover. DNS with a 3,600-second TTL is not in the regional failover path.
- Regional recovery is an automated or operator-driven, documented sequence: detect and declare regional failure, fence the failed region and its writes, promote the cross-region Cloud SQL replica, switch application read/write endpoints, reconfigure Datastream, direct the load balancer to the recovered region, and verify health, data freshness, and writes.
- Client connection-pool behavior, load-balancer convergence, fencing, split-brain prevention, standby backend readiness, and endpoint switching are tested against the 15-minute RTO.

## 6. Database

- Cloud SQL for PostgreSQL uses regional HA for automatic in-region failover. Its HA standby is not used for reporting.
- Dashboards use a separate supported Cloud SQL read replica or an explicitly approved analytics path. Replica lag, capacity, consistency expectations, and behavior during primary or regional failover are documented and monitored.
- A cross-region read replica in europe-west1 is promoted during regional recovery. Replica lag and WAL retention are continuously monitored, with alerts and runbook thresholds tied to the five-minute RPO.
- Backups and point-in-time recovery are enabled. Restore duration is size- and workload-dependent; no fixed five-minute restore claim is made. Restore and promotion times are measured in regular recovery rehearsals.
- The recovery runbook defines the write fence, promotion, endpoint changes, application restart/connection draining, validation, and later failback.

## 7. CDC to BigQuery

- Datastream reads committed changes from Cloud SQL using logical decoding and writes to BigQuery. The objective is that every committed change reaches BigQuery within about five minutes.
- CDC freshness and source replica/WAL lag are separate indicators. Alerts fire before the objective is breached.
- Replication-slot activity, WAL retention, and primary storage growth are monitored with explicit limits and an operational response; Datastream lag must not exhaust primary storage.
- Events are processed idempotently (for example, merge by primary key), and recovery tests verify no unacceptable loss or duplication.
- Regional recovery includes Datastream stop/fence, source and slot handling, destination continuity, restart/cutover, and validation of freshness.

## 8. Security

- Workloads use Workload Identity Federation for GKE, with one least-privilege Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only images built and signed by the approved pipeline.
- BigQuery personal-data columns use policy tags and datasets use customer-managed encryption keys.

## 9. Observability and testing

- SLIs are load-balancer request success rate and latency. Alerts cover one-hour and six-hour error-budget burn, zonal capacity, scheduling failures, autoscaler state, database failover/replica lag, WAL retention, Datastream lag/freshness, and read-replica health.
- A zone-failure game day runs quarterly.
- A full regional recovery rehearsal runs at least annually and records measured RTO, RPO, load-balancer convergence, database promotion time, CDC recovery/freshness, standby serving capacity, connection-pool behavior, and corrective actions.
- Production launch requires passing capacity, upgrade/drain, restore, one-zone-loss, standby-readiness, CDC, and regional-recovery tests against the stated objectives.