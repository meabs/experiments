# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets and availability model

- Customer-facing stateless web/API service, peak 5,000 requests/s, with a monthly end-to-end availability SLO of 99.95% (about 22 minutes of error budget).
- Availability is measured at the load balancer for successful, correctly routed requests. GKE, Cloud SQL, networking, load balancing, failover, and application dependencies are included in the error-budget model; component availability figures are not summed as proof of the SLO.
- The primary platform operates without intervention through loss of one zone.
- Regional loss has a rehearsed recovery objective of RTO 15 minutes and RPO 5 minutes. These are not guarantees until demonstrated by timed tests.

## 2. GKE topology and regional recovery capacity

- The primary environment is a private, regional GKE Standard cluster in `europe-west2`, with nodes across all three zones, separate system and application pools, cluster autoscaling, and explicit minimum/maximum nodes per pool and zone.
- A second-region GKE application environment in `europe-west1` is provisioned before production. It includes tested application capacity, images, configuration, IAM/Workload Identity, networking, quotas, Cloud NAT, secrets, monitoring, database connectivity, and load-balancer backend integration. Its capacity is sufficient for the approved recovery traffic and is exercised in regional-recovery rehearsals; it is not merely created during an incident.
- Use the Regular release channel (Stable may be selected after validating required features and supported versions). Define tested upgrade policies and maintenance windows.
- Use VPC-native networking. Size each pod secondary range from per-node pod masks, maximum nodes, surge capacity, and growth, not a simple pod count. The range must cover the approved maximum (for example, `/18` where appropriate), with utilization alerts and an expansion plan. Validate regional quotas, node capacity, IP capacity, and NAT ports.
- Limit control-plane access to authorized networks.

## 3. Capacity and scheduling

- Initial replica counts and per-pod resource requests are determined by load tests, not an assumed 800 requests/s. Tests cover at least 5,000 requests/s, one-zone loss, pod/node failures, rolling upgrades, dependency latency, CPU, memory, and autoscaler behavior.
- Pre-provision enough capacity that one-zone loss remains within the serving target without depending on timely autoscaler action. Set explicit autoscaler limits and reserve quota and IP capacity for failure and surge conditions.
- Use topology spread constraints across zones. Use required hostname anti-affinity only where placement remains schedulable under failure and upgrade scenarios.
- Each tier has a PDB preserving the tested serving minimum (initially `minAvailable: 5` for six replicas). Emergency and voluntary disruption procedures are separate.
- Node pools use surge upgrades (`maxSurge: 1`, `maxUnavailable: 0` initially), subject to quota and drain tests.

## 4. Traffic and regional recovery

- Use a global external Application Load Balancer with tested backends in both regions and health-based failover. Health checks test meaningful application readiness and dependency behavior without harmful load.
- The recovery runbook declares the incident, fences the failed/old primary, checks replication lag against the RPO decision threshold, promotes the cross-region Cloud SQL replica, switches the application’s database configuration or supported endpoint, validates application readiness and writes, and then permits traffic to the recovery region. Traffic convergence, promotion, reconnection, and smoke tests are measured as one RTO.
- Fencing prevents split-brain: the old primary’s network/application access is blocked or otherwise prevented from accepting writes before promotion. A returning old primary remains isolated, is not reused without reinitialization/reconciliation, and is restored only through an approved failback procedure.
- Do not rely on a 3,600-second DNS TTL. Any auxiliary DNS cutover uses an intentionally low TTL with documented resolver/client caching limitations.

## 5. Cloud SQL

- Cloud SQL for PostgreSQL uses regional HA with automatic zonal failover for the primary. Its HA standby is not used for reads.
- Provision a separate supported read replica for dashboards, size it for reporting load, monitor lag, and define behavior when it is unavailable.
- Provision a cross-region read replica in `europe-west1` for disaster recovery. Monitor replication lag, WAL, and storage. Define a continuously monitored lag threshold, an explicit data-loss decision, and an abort/escalation path when the threshold is exceeded; the five-minute RPO is accepted only when test evidence supports it.
- Enable backups and point-in-time recovery. Report measured, size-dependent restore times. Test restore, promotion, application reconnection, consistency, migration rollback, fencing, and failback.

## 6. CDC to BigQuery

- Datastream uses a supported PostgreSQL logical-decoding configuration. Size and monitor replication slots, WAL retention, storage, restart/replay behavior, and primary CPU/I/O overhead.
- Alerts and safeguards prevent lag or slot retention from exhausting primary storage. A runbook covers pause/resume, failover, slot handling, and safe stream reinitialization.
- Define freshness as source commit-to-queryable time: five-minute target and three-minute warning. Validate inserts, updates, deletes, schema changes, duplicates, ordering, restart recovery, and behavior through database promotion. Use an idempotent design appropriate to each operation; a primary-key merge alone is insufficient for deletes and replay.

## 7. Security and operations

- Use Workload Identity Federation for GKE, one least-privilege service account per tier, and no exported keys.
- Deny cross-namespace traffic by default with network policies. Binary Authorization admits only approved pipeline-built images.
- Protect BigQuery personal-data columns with policy tags and customer-managed encryption keys, with key-access monitoring and recovery procedures.
- Dashboards and alerts cover load-balancer SLIs, one-hour/six-hour burn, zones, scheduling, autoscaling, quotas, NAT, Cloud SQL health/CPU/storage/WAL, replica lag, Datastream slots/lag/freshness, and BigQuery errors.
- Runbooks cover zone loss, regional recovery, database promotion/fencing/failback, CDC failure, restore, and rollback. On-call ownership and escalation are explicit.

## 8. Validation before production

- Complete load, one-zone-loss, quota/IP/NAT, upgrade, regional-failover, promotion/fencing, backup-restore, CDC-correctness, and security tests before launch.
- Demonstrate second-region capacity and complete regional recovery within 15 minutes, including measured traffic convergence, application readiness, observed data loss, and replication lag.
- Run a zone-failure game day at least quarterly and a full regional recovery rehearsal at least annually. Track remediation to closure and reassess the end-to-end availability budget from evidence before declaring the SLO achievable.