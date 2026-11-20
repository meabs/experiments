# Highly available GKE platform with a Cloud SQL analytics feed: design v4

## 1. Targets
- Customer-facing availability SLO is 99.95% monthly, measured end to end at the global load balancer for successful requests and latency. The dependency and change error budget includes load balancing, GKE, application, database, networking, and regional recovery; component SLAs are not multiplied as proof of the SLO.
- The service survives loss of one zone without operator intervention.
- Regional loss has a rehearsed RTO of 15 minutes and RPO of 5 minutes, validated by timed exercises.
- Peak traffic is approximately 5,000 requests per second. The platform is operated by eight engineers using managed services.

## 2. GKE topology and capacity
- A regional GKE Standard cluster runs in europe-west2, with control-plane replication and node pools distributed across all three zones.
- Separate system and application node pools use cluster autoscaling. Minimums, maximums, per-zone limits, quotas, subnet capacity, and upgrade surge capacity are documented and tested.
- The VPC-native cluster uses private nodes, authorized control-plane networks, and regional Cloud NAT.
- The pod secondary range is sized from the configured `maxPodsPerNode`, maximum node count, upgrade surge, and growth headroom. The initial capacity plan uses `maxPodsPerNode: 110`, a maximum of 30 application nodes, and three additional surge nodes. Using the GKE per-node allocation of one `/24` pod block at this setting requires 33 blocks; with 25% growth and operational headroom, at least 42 blocks are required. A `/18` range provides 64 `/24` blocks and is therefore selected initially. The calculation is reviewed if any input changes, and node and pod IP exhaustion are monitored.
- The API is benchmarked at production resource limits. At least seven replicas are provisioned for the 5,000-RPS peak, with additional tested headroom for pod or node failure. Autoscaling targets and scale-up latency are validated.
- Each zone retains explicit spare node capacity so surviving zones can carry peak traffic after loss of one zone, while retaining headroom for node failure and autoscaler delay.

## 3. Release and workload disruption
- The cluster uses the Regular release channel (Stable may be selected if required features permit), with a documented maintenance window and release validation/rollback process.
- Stateless tiers use topology spread constraints across zones and required hostname anti-affinity where one-replica-per-node placement is required. Placement is verified under normal and degraded capacity.
- The API tier initially runs seven replicas. Its PodDisruptionBudget initially uses `minAvailable: 6`, subject to validation against the final capacity plan; other tiers use budgets that preserve degraded-zone service while allowing maintenance.
- Node pools use surge upgrades with controlled disruption. Upgrade completion and drain behavior are tested with PDBs and placement rules.

## 4. Traffic and regional recovery
- A global external Application Load Balancer has backends in both regions and uses documented health-based regional failover. Health checks test meaningful application and database readiness, not merely process liveness.
- The recovery backend remains unready until database fencing, promotion, application endpoint switching, and readiness validation complete. DNS is not relied upon for the 15-minute objective; any DNS TTL and client-cache limitations are documented.
- The second region is a warm, continuously deployable recovery environment with tested GKE capacity, networking, IAM, secrets, images, configuration, and observability.
- Runbooks define detection, database promotion, fencing of the failed primary, endpoint switching, traffic failover, validation, rollback, and failback. The complete path is rehearsed annually and timed against the 15-minute RTO.

## 5. Cloud SQL
- Cloud SQL for PostgreSQL uses HA for the primary regional instance with automatic zonal failover.
- The HA standby is not used for reads. Analytics uses a separately provisioned supported read replica, sized and monitored for dashboard workload, replication lag, and failure behavior.
- A cross-region read replica in europe-west1 supports regional recovery. Lag is continuously monitored against the 5-minute RPO. Promotion, fencing, credentials, endpoint switching, and split-brain protection are documented and tested.
- Backup/PITR restore time is measured for representative database sizes. Tested restore and promotion timings, retention, and achievable RTO/RPO are recorded; no size-independent five-minute restore claim is made.

## 6. Change data capture and BigQuery
- Datastream uses the supported Cloud SQL logical replication configuration and is tested for primary CPU, I/O, and transaction impact.
- End-to-end freshness is measured from commit through queryable BigQuery availability, with a target of approximately five minutes and alerts at three minutes. Destination controls must not permit routine staleness beyond this objective.
- Alerts cover source-to-destination lag, end-to-end freshness, replication-slot/WAL retention, Cloud SQL storage growth, and Datastream errors.
- Slot growth has explicit thresholds and an operator runbook. Datastream is paused, throttled, or remediated before retained WAL can exhaust primary storage or threaten transactional availability.
- If CDC is throttled or paused, the incident is escalated immediately to the on-call engineer and service owner; freshness and WAL/RPO risks are surfaced on the operational dashboard and incident channel. Operators protect the primary first, record the resulting freshness-SLO breach, restore CDC or perform a controlled resynchronization, and verify destination completeness before closing the incident. Sustained lag triggers capacity remediation or a documented recovery decision.
- Destination writes are idempotent, using stable change identity and merge semantics where appropriate, so retries do not create duplicate rows.

## 7. Security
- Workloads use Workload Identity Federation for GKE, with a least-privilege Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only images built and signed by the approved pipeline.
- BigQuery personal-data columns use policy tags, and datasets use customer-managed encryption keys. Secrets are replicated and access-controlled in both recovery regions.

## 8. Observability and testing
- SLIs are load-balancer request success rate and latency, with one-hour and six-hour error-budget burn alerts.
- Dashboards and alerts cover zonal capacity, pod placement, autoscaler state, quotas/IP exhaustion, Cloud SQL health and lag, cross-region replica lag, backup/restore status, Datastream freshness and slot/WAL retention, and global failover health.
- A zone-failure game day runs quarterly. A full regional recovery rehearsal runs annually, including database promotion, endpoint switching, traffic failover, and restoration of normal operations. Reports record measured capacity, RTO, RPO, CDC freshness, and corrective actions.