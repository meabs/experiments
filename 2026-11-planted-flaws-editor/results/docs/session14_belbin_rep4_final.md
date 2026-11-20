# Highly available GKE platform with Cloud SQL analytics feed: design v3

Written by Agent I, platform lead.

## 1. Targets and availability

- Customer-facing end-to-end availability target is 99.95% per month (approximately 22 minutes of error budget), measured by load-balancer request success and latency.
- Peak traffic is approximately 5,000 requests/second. The eight-person team uses managed services.
- The service tolerates loss of one zone without operator intervention.
- Regional recovery is operator-controlled, documented, and rehearsed, with target RTO 15 minutes and RPO 5 minutes. These are acceptance criteria, not assumptions.
- Every committed database change should reach BigQuery in approximately five minutes without unsafe primary-database load.
- Availability is assessed end-to-end. Component availability is not multiplied or treated as sufficient evidence; dependency redundancy, failure domains, and measured SLIs are required.

## 2. GKE topology and capacity

- One regional GKE Standard cluster is deployed in europe-west2, with control plane and node pools distributed across all three zones.
- Separate system and application pools use cluster autoscaling.
- The pod secondary range is sized from maximum nodes, pod density, upgrade surge, and autoscaler headroom; it is at least /19 for the planned maximum, with a documented expansion plan. A /22 is not used.
- Nodes are private, control-plane access is restricted, and internet egress uses monitored Cloud NAT with regional Cloud Router.
- The Stable release channel is used where required features are supported. A weekly maintenance window, exclusions, and upgrade testing are documented.
- Six API replicas provide capacity above 5,000 requests/second based on representative load tests. Each zone is initially sized for approximately 60% peak utilisation. Reserved quota and autoscaler headroom must permit replacement nodes after zone loss without intervention.
- Tests cover peak load, rolling upgrades, surge nodes, zone loss, pod startup, load-balancer behavior, quotas, IP ranges, autoscaling, and database limits.

## 3. Placement and disruption

- Stateless tiers have at least six replicas and topology spread constraints across zones (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Preferred hostname anti-affinity may be used; required anti-affinity is used only where post-zone-loss capacity has been demonstrated.
- Each tier has a drainable PodDisruptionBudget, initially `minAvailable: 5` for six replicas. It must not be set to all replicas and is revisited after testing.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to pod-range, quota, and capacity checks.
- Readiness, termination grace, preStop handling, and connection draining are tested.

## 4. Traffic and regional recovery

- A global external Application Load Balancer has a backend in each region and performs health-based regional failover directly; DNS is not the failover mechanism. Any DNS used in front has a low TTL and its caching is included in measurements.
- Health checks verify application readiness, required dependencies, database writability, and recovery state. The secondary backend remains unhealthy until its database is promoted, fencing is verified, writes are enabled, and application readiness checks pass.
- Regional failover is operator-controlled. The runbook requires: stop or fence writes to the failed primary; inspect replica lag; make an explicit promotion decision; promote the cross-region replica; switch application configuration; verify writable/read consistency; restart and reconcile CDC; and only then enable the secondary backend.
- Split-brain prevention and rollback considerations are documented. The rehearsal measures detection, fencing, promotion, configuration switch, application readiness, traffic shift, and client reconnection against the 15-minute RTO. The promotion gate requires measured lag within the five-minute RPO; otherwise an explicit data-loss decision is required.

## 5. Database

- Cloud SQL for PostgreSQL uses HA with primary and automatic failover standby in separate zones. The HA standby is not a read endpoint.
- Analytics uses a separately provisioned supported read replica or equivalent validated analytics path. Replica lag, capacity, failover behavior, and primary impact are monitored; dashboards tolerate lag and fall back appropriately.
- A cross-region asynchronous read replica in europe-west1 is the regional recovery target. Lag and measured RPO are continuously monitored.
- Automated backups and point-in-time recovery are enabled. Restore RTO/RPO are size- and workload-dependent, established from representative backups, and tested regularly. Restore is a fallback, not the primary 15-minute regional recovery path.

## 6. CDC and BigQuery

- Datastream uses supported logical decoding and writes to BigQuery. Peak-write tests verify that CPU, storage, connections, replication slots, WAL retention, disk growth, and replication lag cannot endanger the primary. Slot/WAL alarms and backpressure safeguards are mandatory.
- The CDC freshness objective is five minutes, with alerts at three minutes and escalation for sustained lag. A 15-minute destination staleness limit is not used to claim five-minute freshness.
- Events are idempotent, using primary-key merge and ordering/version handling.
- The runbook covers interruption, restart, backfill, duplicate handling, reconciliation, and behavior during database promotion. Post-recovery freshness and completeness are verified.

## 7. Security

- Workloads use Workload Identity Federation, one least-privilege service account per tier, and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only approved signed images.
- BigQuery personal-data columns use policy tags; datasets use customer-managed encryption keys with documented access, rotation, and recovery procedures.

## 8. Acceptance and operations

Before production, recorded evidence must demonstrate:

- peak-load capacity and end-to-end 99.95% SLO instrumentation;
- continued serving and scheduling after one-zone loss;
- successful surge upgrades and drains;
- Cloud SQL HA failover;
- cross-region replica lag within the five-minute promotion gate;
- operator-controlled fencing, promotion, configuration cutover, and readiness-gated load-balancer failover within 15 minutes;
- Datastream freshness of approximately five minutes under peak writes, including slot/WAL safeguards, restart, promotion, and reconciliation;
- backup restore RTO/RPO for representative database sizes.

A zone-failure game day runs at least quarterly. Regional recovery runs at least annually and after material architecture changes. Backup restore and CDC reconciliation run on a documented schedule. Every exercise records measured RTO/RPO, data loss, limitations, corrective actions, and owners.