# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets and service objectives

- End-to-end customer-facing availability SLO is 99.95% monthly, measured at the global load balancer, including GKE, load balancing, Cloud SQL, networking, DNS/client caching where applicable, deployments, and regional recovery.
- The platform tolerates loss of one zone without operator action.
- Regional loss has a rehearsed RTO of 15 minutes and target RPO of 5 minutes. The asynchronous cross-region replica’s lag is continuously measured; RPO is unmet when lag exceeds five minutes.
- Peak traffic is approximately 5,000 requests/second. The platform is operated by eight engineers using managed services.

## 2. GKE and networking

- Use one regional GKE Standard cluster in europe-west2, with control planes and node pools across all three zones.
- Use separate system and application pools with cluster autoscaling. Before build, reserve and validate quotas and capacity for maximum nodes after one-zone loss, autoscaler headroom, and upgrade surge; recovery is not assumed instantaneous.
- Use private VPC-native nodes, restricted control-plane access, and Cloud NAT for internet egress.
- Size pod secondary ranges from `maxPodsPerNode`, maximum nodes per pool, autoscaler headroom, surge, and growth using GKE’s per-node allocation model. The initial `/22` is rejected.
- Use the Regular release channel unless compatibility testing demonstrates a required feature elsewhere. Define maintenance exclusions and retain the Sunday maintenance window where compatible.

## 3. Capacity and placement

- Run at least six API replicas, with load testing demonstrating capacity above 5,000 requests/second and reserve.
- Use topology spread constraints (`maxSkew: 1`, `DoNotSchedule`) across zones and hostname anti-affinity as an additional preference.
- Use a PDB such as `minAvailable: 5` for six replicas, validated against zone loss, upgrades, and surge capacity.
- Use node-pool surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to quota validation.

## 4. Traffic and regional recovery

- Use a global external Application Load Balancer with explicitly configured primary and backup regional backends and health-based failover. DNS changes are not part of failover; any DNS access path has tested TTL and documented resolver/client limitations.
- Health checks represent useful serving readiness, including defined database-dependency behavior, without causing both regions to fail closed. Test failover, draining, and reconnects.
- The recovery runbook detects and fences the failed/old primary, checks replica lag, promotes the Cloud SQL replica only when lag is at most five minutes, updates the application endpoint/configuration, validates a successful write and CDC, and enables the recovered regional backend. It must complete within 15 minutes and prevent split brain.

## 5. Cloud SQL

- Use Cloud SQL for PostgreSQL HA for the regional transactional primary. Its HA standby is not a reporting endpoint.
- Use a separately sized supported read replica, or BigQuery where appropriate, for dashboards. Monitor capacity, lag, errors, query impact, and define separate analytics SLOs.
- Maintain an asynchronous cross-region read replica in europe-west1. Monitor lag continuously and alert before the five-minute threshold. Document promotion prerequisites, fencing, endpoint/secret changes, reconnect behavior, and consequences when the objective is missed.
- Keep automated backups and PITR enabled. Establish measured, database-size-dependent restore RTO/RPO objectives through scheduled restore tests; make no unconditional five-minute restore claim.

## 6. CDC to BigQuery

- Configure and validate Datastream logical decoding for Cloud SQL PostgreSQL. Normal committed-change freshness target is approximately five minutes without endangering the primary.
- Monitor freshness, errors, replication-slot retention, WAL growth, and primary CPU/I/O/load. Define bounded-growth alerts and a safe throttle/stop procedure if primary health is threatened.
- Apply events idempotently, document update/delete semantics, and test duplicate, delayed, and out-of-order events. Define BigQuery freshness and cost controls compatible with the objective.

## 7. Security, observability, and testing

- Use Workload Identity Federation, one Google service account per tier, no exported keys, default-deny namespace network policies, and Binary Authorization.
- Protect personal-data columns with BigQuery policy tags and customer-managed encryption keys.
- Dashboards and alerts cover end-to-end SLO/error-budget burn, backend health, database availability, all replica lag, CDC freshness/WAL growth, zonal capacity, quotas, autoscaling, PDBs, and upgrades. Maintain separate objectives for the analytics replica, cross-region replica, and Datastream.

Acceptance evidence is a build gate, recorded by:
- **Platform owner:** secondary-range calculation; reserved quota and post-zone-loss scheduling; upgrade surge; zone-loss capacity test. Pass requires scheduling the required service capacity without operator action.
- **Networking/platform owner:** primary/backup LB health semantics, failover, draining, and reconnect test. Traffic failover must not route to a non-ready or non-writable region.
- **Database owner:** promotion, fencing, endpoint cutover, reconnect, and successful-write test. Complete regional recovery must be ≤15 minutes; promotion is permitted only at lag ≤5 minutes. Restore tests must record measured RTO/RPO by database size.
- **Data/CDC owner:** peak-load analytics-replica and cross-region lag tests, Datastream freshness, slot/WAL bounds, and primary-load safeguards. Freshness and lag targets are five minutes.
- **SRE:** records results, monitors error budgets, and approves quarterly zone game days and annual regional rehearsals.

If lag exceeds five minutes, the database owner refuses promotion, fences traffic, escalates to SRE/platform leadership, and documents an emergency decision. The fallback is continued fencing/read-only operation or a documented emergency promotion with explicitly accepted data loss; it is not silent promotion. Retain test reports and update runbooks.