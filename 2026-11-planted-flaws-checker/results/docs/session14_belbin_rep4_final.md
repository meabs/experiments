# Highly available GKE platform with Cloud SQL analytics feed: design v3

Written by Agent I, platform lead.

## 1. Targets and assumptions

- End-to-end availability target is 99.95% per month (approximately 22 minutes downtime), with an explicit error budget covering GKE, load balancing, Cloud SQL, networking, dependencies, and failover. Managed-service availability targets are inputs, not independent guarantees that compose to 99.95%.
- The service must survive loss of one zone without operator action.
- Regional loss has a documented and rehearsed recovery in a second region, with measured RTO ≤15 minutes and measured database RPO ≤5 minutes.
- Peak traffic is approximately 5,000 requests/second. All capacity, quota, IP-range, and autoscaler limits are acceptance-tested rather than inferred.

## 2. GKE topology

- One regional GKE Standard cluster in europe-west2, with control plane replication across three zones and node pools in all zones.
- Separate system and application pools, both with cluster autoscaling. Maximum node counts, quotas, surge capacity, and growth headroom are recorded before build.
- The cluster is VPC-native with private nodes. The pod secondary range is sized from GKE’s documented per-node allocation for the configured `maxPodsPerNode`, maximum nodes, surge, and growth headroom—not from raw pod count. The current 30-node plan is at least /20, with the final range (likely /18 or larger if GKE allocates /24 per node) confirmed before build.
- Control-plane access is restricted to authorised networks. Internet egress uses Cloud NAT through a regional Cloud Router.
- Production uses the Regular release channel, with a Sunday 02:00–06:00 local maintenance window.

## 3. Capacity and placement

- API pods serve approximately 800 requests/second under the tested workload. The baseline is at least eight replicas, providing over 5,000 requests/second before failure and rollout headroom; the exact count is set by load testing.
- Required topology spread constraints distribute replicas across zones (`maxSkew: 1`, `DoNotSchedule`). Required or otherwise verified anti-affinity is used where needed; preferred anti-affinity is not treated as a placement guarantee.
- Node pools, quotas, pod ranges, and autoscaler limits are provisioned so the tested baseline can run after loss of one zone without emergency capacity. Post-zone-loss utilisation and scale-up time are measured in a game day; no untested 90% utilisation assumption is used.

## 4. Disruption and health

- Each stateless tier has a PDB with `minAvailable: 5` initially, subject to capacity-test results. This preserves serving capacity while permitting voluntary maintenance.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`.
- Liveness and readiness are separate. Load-balancer health checks use a bounded readiness endpoint proving that the serving path is available. Database checks prevent accepting writes when the write path is unavailable, without unnecessarily withdrawing healthy read/serve capacity. Semantics are tested during promotion and failover.
- Zone-loss, scaling, rollout, and PDB behavior are tested before production.

## 5. Traffic and regional recovery

- A global external Application Load Balancer has a backend in each region, with explicitly configured health-based regional failover and 60-second connection draining. DNS TTL is not relied upon for the 15-minute RTO.
- Recovery runbook: detect and declare regional failure; fence or freeze writes to the old primary; promote the cross-region Cloud SQL replica; switch application write endpoints and credentials; refresh connection pools; validate data freshness and read/write health; route traffic through the global load balancer; then resume writes.
- The old primary is prevented from accepting writes, and rollback and communication steps are documented.
- The complete sequence, including draining, is rehearsed and must demonstrate RTO ≤15 minutes.

## 6. Cloud SQL

- Cloud SQL for PostgreSQL is deployed in europe-west2 with HA enabled and automated backups/PITR. The HA standby is not a query endpoint.
- Dashboards use a separately provisioned supported read/reporting replica. Its capacity, lag, freshness, and failure behavior are monitored; analytics load cannot overload the transactional primary.
- A cross-region read replica in europe-west1 is the regional recovery target. Replication lag is continuously monitored. Observed lag ≤5 minutes at promotion is an acceptance criterion; promotion is blocked or explicitly approved with recorded recovery/data-loss status when it exceeds that threshold.
- Restore, PITR, corruption recovery, and migration rollback objectives are measured at production database size and workload. No unconditional five-minute restore claim is made.

## 7. CDC and BigQuery

- Datastream reads changes from the Cloud SQL primary using a supported logical-decoding configuration and writes to BigQuery without reporting queries on the primary.
- Normal and post-failover Datastream-to-BigQuery freshness must be ≤5 minutes, separately from the database RPO. Freshness alerts fire at three minutes. Failover behavior, restart/resume, source reconfiguration, and duplicate handling are tested.
- Replication-slot/WAL growth is monitored with alarms and an explicit response before primary storage is endangered.
- BigQuery applies events with an idempotent primary-key merge. Its 15-minute staleness limit controls query cost and does not replace the five-minute freshness objective.

## 8. Security and observability

- Workloads use Workload Identity Federation for GKE, one Google service account per tier, and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only approved-pipeline images.
- BigQuery personal-data columns use policy tags and customer-managed encryption keys.
- Dashboards and alerts cover request success/latency, error-budget burn, regional backend health, node and quota capacity, autoscaling, Cloud SQL HA and cross-region lag, reporting-replica lag, Datastream freshness/WAL growth, and recovery status.

## 9. Acceptance and operations

- Before launch, load-test at least eight replicas through a zone loss; verify placement, quotas, IP space, autoscaling, and serving capacity.
- Quarterly zone-failure game days and at least annual regional-recovery rehearsals are required.
- Acceptance evidence must include measured end-to-end availability assumptions, zone-loss capacity, cross-region lag/RPO, restore time at production size, reporting-replica behavior, Datastream freshness during failover, and the complete fencing → promotion → endpoint/connection-pool switch → load-balancer routing sequence within 15 minutes.
- Reports track corrective actions, and production claims are updated only from test evidence.