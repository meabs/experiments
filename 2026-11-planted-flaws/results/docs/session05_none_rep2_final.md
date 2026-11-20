# Highly available GKE platform with Cloud SQL analytics feed: design v3

## 1. Objectives and SLOs

- End-to-end customer availability SLO is 99.95% per calendar month, including load balancing, GKE, Cloud SQL, networking, dependencies, and planned maintenance. This is not derived by summing provider SLAs; dependencies and error budgets are modeled explicitly.
- Monthly error budget is approximately 22 minutes. Alerts measure request success rate and latency at the load balancer using one-hour and six-hour burn-rate windows.
- The platform tolerates loss of one zone without operator intervention.
- Regional recovery is rehearsed to a measured RTO of 15 minutes and RPO of 5 minutes. RTO includes fencing, database promotion, application reconfiguration, validation, and traffic enablement.
- Peak traffic is approximately 5,000 requests per second. Capacity, quotas, and failover are validated by load tests and game days.

## 2. GKE topology and operations

- A regional GKE Standard cluster runs in europe-west2, with control-plane replication and node pools across all three zones.
- Separate system and application node pools use the Regular release channel with a tested maintenance policy and window.
- Nodes are private; the control-plane endpoint is restricted to authorized networks. Internet egress uses Cloud NAT.
- A warm, pre-provisioned GKE cluster/backend exists in a second region, with replicated images, configuration, secrets, quotas, and sufficient tested recovery capacity.
- Workload identities use one Google service account per tier; exported keys are prohibited. Binary Authorization and namespace-default-deny network policies are enabled.

## 3. Capacity and placement

- Resource requests and limits, node maximums, regional quotas, and autoscaler behavior are documented and tested.
- Both regions retain tested N+1 capacity. The design does not rely on autoscaler reaction time or outage-time capacity allocation.
- Stateless services normally run at least six replicas with required zone topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`). Required hostname anti-affinity is used only where needed and is validated against capacity.
- A PDB preserves tested minimum serving capacity (initially `minAvailable: 5` for six replicas) without blocking every voluntary eviction. Node-pool upgrades use surge capacity and are load-tested.
- Zone-loss, rolling-upgrade, quota-exhaustion, and autoscaler scenarios are tested; minimum serving capacity and latency are recorded.

## 4. Traffic and regional recovery

- A global external Application Load Balancer has backends in both regions and uses health-based failover/traffic steering. DNS is not the recovery mechanism; any fallback uses a low, tested TTL and documents resolver caching limitations.
- Backend readiness is database-aware. A process-only `/healthz` cannot mark a region healthy when its application cannot safely use the promoted database.
- The recovery backend remains gated until the runbook has:
  1. Fenced or stopped writers in the failed region and confirmed the old writer cannot accept traffic.
  2. Promoted the cross-region Cloud SQL replica.
  3. Validated replica lag and resulting RPO.
  4. Reconfigured application clients, secrets, and connection endpoints.
  5. Reconfigured and validated Datastream.
  6. Performed controlled write/read validation.
  7. Marked the backend ready and enabled load-balancer traffic.
- During fencing and promotion, fencing establishes a consistency boundary: the application uses one authoritative writer endpoint and rejects or clearly degrades writes until the promoted database passes validation. In-flight requests, queued jobs, sequences, and transactions from the fenced region are explicitly handled at fencing/promotion. CDC reconciliation covers acknowledged changes at that boundary, including inserts, updates, deletes, ordering, duplicates, and gaps.
- Rollback, operator ownership, and failure handling are documented. The complete sequence is timed in annual regional rehearsals and must meet the 15-minute RTO.

## 5. Cloud SQL

- Cloud SQL for PostgreSQL uses regional HA for the primary, with automatic in-region failover. The HA standby is not a readable analytics endpoint.
- Dashboards use a separately sized, supported read replica or another supported analytics path. Replica lag, capacity, consistency expectations, and failure behavior are monitored.
- A cross-region read replica in europe-west1 is the recovery target. Its asynchronous lag is continuously measured and alerted before it threatens the five-minute RPO.
- Promotion, fencing, client reconfiguration, validation, and rollback are part of the rehearsed runbook.
- Automated backups and point-in-time recovery are enabled. Restore time is measured for realistic database sizes and is not assumed to be five minutes or size-independent. Backup recovery is separate from regional replica promotion.

## 6. CDC and BigQuery

- Datastream reads PostgreSQL changes without endangering the primary. Replication-slot/WAL retention, storage growth, and backpressure are bounded and alerted so CDC outage cannot exhaust primary storage.
- Freshness is measured from database commit timestamp to a queryable BigQuery row and is about five minutes. Alerts fire early enough for recovery; a 15-minute staleness setting is not treated as satisfying the requirement.
- Datastream reconnect and checkpoint/replay behavior across Cloud SQL failover and regional promotion are tested. WAL retention preserves changes during outages within documented limits.
- Inserts, updates, deletes, ordering, replay, and duplicates are handled with idempotent processing and reconciliation. A primary-key merge alone is not claimed to provide exactly-once delivery.
- During CDC degradation, dashboards expose freshness and documented degraded-mode behavior. Recovery includes replay and reconciliation, with no acknowledged committed change silently discarded.

## 7. Security and data protection

- Workloads access Google APIs through Workload Identity Federation for GKE, with no exported service-account keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only pipeline-built images.
- BigQuery personal-data columns use policy tags; datasets use customer-managed encryption keys. Secrets and required configuration are replicated to the warm recovery region under controlled access.

## 8. Observability and testing

- Dashboards cover end-to-end availability and latency, Cloud SQL HA and cross-region lag, Datastream commit-to-queryable freshness, WAL/slot retention, BigQuery load health, node capacity by zone and region, quotas, and autoscaler state.
- Alerts cover SLO burn rate, replica lag against the five-minute RPO, CDC freshness before five minutes, storage/slot growth, and recovery readiness.
- Zone-failure and maintenance-capacity game days run quarterly. A full regional recovery rehearsal runs at least annually, including fencing, database promotion, application reconfiguration, CDC restart/reconciliation, readiness gating, and traffic enablement. Each produces a written report with measured RTO, RPO, capacity, and corrective actions.