# Highly available GKE platform with a Cloud SQL analytics feed: design v2

Written by Agent I, platform lead.

## 1. Targets and service level

- Customer-facing stateless web/API service, peak 5,000 requests/second.
- End-to-end availability objective is 99.95% monthly, with an explicit dependency budget covering the load balancer, GKE, application, Cloud SQL, networking/NAT, and regional-failover operations. Individual managed-service availability figures are not assumed to compose automatically.
- The platform survives loss of one zone without intervention.
- Loss of a region has a documented and rehearsed recovery with a 15-minute RTO and a measured, monitored RPO target of five minutes. The RPO is an acceptance criterion, not an assumption about asynchronous replication.
- Every committed change should reach BigQuery within approximately five minutes without endangering the transactional primary.

## 2. Cluster and network topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across three zones and node pools in all three zones.
- Separate system and application node pools, both with cluster autoscaling enabled.
- Use a pod secondary range sized from the configured max-pods-per-node, maximum node count, and growth headroom; it must support at least 30 nodes and their allocated pod ranges (not merely 1,024 addresses). Size a separate services range appropriately.
- VPC-native private nodes; control-plane access is restricted to authorised networks.
- Internet egress uses Cloud NAT on a regional Cloud Router.
- Use the Regular GKE release channel (or an organisation-approved Stable channel if all required features are available). Maintenance windows and upgrades are validated in staging and rehearsed before production rollout.

## 3. Capacity

- Baseline at least seven API replicas, since six replicas at 800 requests/second provide less than the 5,000-request/second peak. Validate replica capacity, autoscaling thresholds, node capacity, and latency with load testing, with documented headroom.
- Each zone is sized for normal peak load at approximately 60% utilisation. After loss of one zone, the remaining zones must carry traffic within tested capacity while autoscaling adds nodes.
- Capacity tests are repeated after material workload or configuration changes.

## 4. Placement and disruption

- Stateless tiers use topology spread constraints across zones with `maxSkew: 1` and `whenUnsatisfiable: DoNotSchedule`.
- Use required hostname anti-affinity where one replica per node is a requirement; otherwise document that preferred anti-affinity is best effort.
- PodDisruptionBudgets are capacity-tested and permit maintenance; the initial policy is `minAvailable: 5` for a six-replica tier, adjusted consistently if the replica baseline changes.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to successful staging and production upgrade rehearsals.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with healthy backends in each region.
- Regional routing uses the load balancer’s health-based backend failover, not a 3,600-second DNS update. Any DNS used by clients has a TTL and cache limitation documented separately.
- Health checks use an endpoint that verifies serving readiness without depending on an unavailable database operation. Connection draining is 60 seconds.
- The regional-recovery runbook provisions or activates the secondary application, promotes the Cloud SQL cross-region replica, switches the application’s write endpoint, and prevents split-brain through fencing/endpoint controls and verification of the old primary before writes are enabled.
- The runbook measures failover time and confirms application, database, load-balancer, and CDC recovery within the RTO.

## 6. Database

- Cloud SQL for PostgreSQL uses regional HA with automatic in-region failover.
- The HA standby is not used for reads. Analytics dashboards use a separately provisioned supported read replica or reporting path, with capacity and lag monitored.
- A cross-region read replica in europe-west1 is the regional-recovery target. Its replication lag, promoteability, and data-loss behavior are monitored continuously.
- The five-minute RPO is accepted only after repeated recovery rehearsals demonstrate the required measured lag and promotion behavior, including an explicit response when lag exceeds the target.
- Backup and point-in-time recovery remain enabled. Restore time is size- and workload-dependent; define a measured restore objective for the production database and validate it in scheduled rehearsals rather than asserting a universal five-minute restore.

## 7. Change data capture and BigQuery

- Datastream reads changes from the Cloud SQL primary through supported logical-decoding configuration and writes them to BigQuery.
- Target freshness is approximately five minutes; alert at three minutes and monitor replication slots, source load, errors, and backlog.
- Protect the primary with tested CDC configuration, quotas, and load limits.
- BigQuery staleness and cost controls are documented; the 15-minute staleness limit is retained only if it does not conflict with the freshness objective.
- Idempotent merge/application behavior prevents duplicate change events from creating duplicate rows.
- The recovery rehearsal tests Datastream behavior during database promotion, including source reconfiguration, slot handling, restart/resnapshot requirements, and restoration of the five-minute freshness objective.

## 8. Security

- Workloads use Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default.
- Binary Authorization admits only images built by the approved pipeline.
- BigQuery personal-data columns use policy tags, and datasets use customer-managed encryption keys.

## 9. Observability and acceptance criteria

- SLIs are load-balancer request success rate and latency, with one-hour and six-hour error-budget burn alerts.
- Dashboards and alerts cover regional capacity, node-pool capacity by zone, autoscaler state, Cloud SQL health and replication lag, read-replica lag, cross-region lag, Datastream freshness/slot health, and BigQuery staleness.
- The platform is not accepted for build completion until load, zone-failure, upgrade, database-promotion, regional-recovery, restore, and Datastream-restart rehearsals demonstrate the documented availability, capacity, RTO, RPO, and freshness criteria.

## 10. Testing

- Conduct a zone-failure game day at least quarterly.
- Conduct a full regional recovery rehearsal at least annually and after material architecture changes.
- Record measured results, gaps, and remediation owners in a written report; update the runbooks and acceptance criteria from the results.