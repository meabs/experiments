# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets and service-level objectives

- The customer-facing platform SLO is 99.95% monthly availability, measured by successful, correctly routed requests at the global load balancer. This allows approximately 22 minutes of monthly unavailability.
- GKE, Cloud SQL, load balancing, networking, and application dependencies are separate contributors; their availability figures are not multiplied or assumed to compose to 99.95%. The platform owns the resulting error budget.
- The service must tolerate loss of one zone without operator intervention.
- Loss of the primary region requires documented and rehearsed recovery in `europe-west1`. The target RTO is 15 minutes, conditional on tested database size, replica lag, and recovery procedure. The target RPO is five minutes, conditional on measured asynchronous replica lag; it is not a guarantee.
- Peak traffic is approximately 5,000 requests/second. Capacity must include retries, startup time, autoscaler delay, and one-zone loss.
- Every committed database change should reach BigQuery within five minutes under normal operation. This is a measured freshness SLO, not a guarantee during an unbounded outage or CDC reconfiguration.

## 2. Cluster and node topology

- Use a regional GKE Standard cluster in `europe-west2`, with nodes distributed across all three zones. Use the Regular release channel, or Stable if required features are available, with compatibility testing, staged upgrades, rollback, and a defined maintenance window.
- Continuously provision a second, capacity-tested regional GKE Standard cluster in `europe-west1`. Synchronize images, configuration, secrets, quotas, and deployment state; it must not be created during an incident. Confirm GKE and Cloud SQL availability and feature compatibility for `europe-west1` before provisioning.
- Before cluster creation, record maximum and minimum node counts for every pool and zone, regional and per-zone CPU/memory/IP quotas, reserved quota headroom, and autoscaler limits. The approved capacity sheet is a build gate owned by the platform lead.
- Use separate system and application node pools. Configure autoscaling per pool and zone, with quota reservations and surge capacity for upgrades and one-zone loss.
- Size the VPC-native Pod secondary range from the configured `maxPodsPerNode`, GKE per-node Pod CIDR allocation, maximum node count, surge nodes, and headroom. Do not use `/22`; the current planning baseline is `/18`, subject to the signed IP plan. The IP plan must state the resulting maximum nodes, allocated Pod CIDR per node, unused headroom, and expansion method before creation.
- Use private nodes and restrict control-plane access to authorized networks. Use Cloud NAT with regional redundancy as supported by the chosen design, and monitor NAT port and capacity utilization.

## 3. Capacity and placement

- Six replicas at 800 requests/second provide only 4,800 requests/second and are insufficient for the stated peak. Set replica counts, per-zone node counts, requests, limits, and autoscaler bounds from load-test results.
- The pre-build capacity gate must record tested sustained throughput, peak throughput including retries, p95/p99 latency, normal utilization, and utilization and throughput after loss of any one zone. The result must demonstrate 5,000 requests/second with operational headroom; approximately 90% post-loss utilization is not an acceptable default.
- Record normal and post-zone-loss node counts, quotas, scheduling headroom, and the maximum measured replacement-node recovery time for both regions. The standby region must meet the same acceptance criteria needed for regional traffic.
- Use topology spread constraints across zones with `DoNotSchedule`. Use required hostname anti-affinity only where feasible; otherwise document the weaker guarantee. Test scheduling with a zone unavailable and during upgrades.
- Use a feasible PDB, such as `minAvailable: 5` for six replicas only if load tests demonstrate the required SLO. The PDB must permit controlled voluntary disruption.

## 4. Traffic and regional recovery

- Deploy capacity-tested application stacks in both regions. The global external Application Load Balancer uses health-based regional failover. Health checks test serving readiness, not merely process liveness; define whether database unavailability makes a backend unready.
- Do not rely on a 3,600-second DNS TTL. Test connection draining, retries, long-lived connections, and traffic convergence.
- The recovery runbook must:
  1. Detect and declare regional failure.
  2. Fence or otherwise prevent writes to the old primary.
  3. Verify cross-region replica lag and record the potential data-loss interval.
  4. Promote the recovery-region replica.
  5. Update endpoints, credentials, secrets, and configuration.
  6. Reconfigure and validate Datastream from the promoted database.
  7. Validate application health, data integrity, and CDC freshness.
  8. Shift global load-balancer traffic and monitor.
  9. Define rollback, old-region rejoin, and split-brain prevention.
- The recovery acceptance gate must record measured fencing, promotion, credential/configuration cutover, CDC recovery, traffic convergence, and total RTO times. A 15-minute RTO is accepted only if the rehearsal demonstrates it for the recorded database size and lag.
- Rehearse this procedure at least annually and record results. No regional-recovery SLO is approved from design claims alone.

## 5. Cloud SQL

- Use Cloud SQL for PostgreSQL with regional high availability. The HA standby is for failover and is not an analytics read endpoint.
- Provision a separate supported read replica for dashboards, sized and load-tested for reporting traffic. Before production, record its lag warning and failure thresholds and define dashboard behavior when thresholds are exceeded.
- Provision an asynchronous cross-region read replica for disaster recovery. Monitor lag continuously and alert before the five-minute RPO objective is exceeded. The acceptance record must include measured lag under normal and peak write load and the expected data-loss interval during promotion.
- Enable automated backups and point-in-time recovery. Restore objectives are database-size-dependent and must be measured through restoration tests.
- Fence application writes during promotion. Test connection pooling and stale endpoint behavior during failover.

## 6. Change data capture to BigQuery

- Configure Datastream with PostgreSQL logical-decoding and replication-slot prerequisites. Confirm that the configuration does not impose unacceptable primary overhead.
- Monitor source lag, destination freshness, replication-slot activity, WAL retention, disk growth, errors, and backpressure. Alert and provide a runbook for stalled consumers and excessive WAL accumulation.
- Target five-minute end-to-end freshness under normal operation, with a three-minute warning threshold. Record measured freshness under peak load before production.
- Handle inserts, updates, deletes, ordering, retries, duplicates, schema changes, and replay explicitly. Verify idempotency; a primary-key merge alone does not prove ordering or delete correctness.
- Document behavior during HA failover and regional promotion, including slot recreation or reassignment, duplicate/replayed events, and validation before declaring CDC recovered.
- BigQuery may be up to 15 minutes stale during approved degraded operation, but the normal-operation freshness SLO remains five minutes.

## 7. Security

- Use Workload Identity Federation for GKE, one least-privilege Google service account per tier, and no exported keys.
- Deny cross-namespace traffic by default with NetworkPolicy and allow only documented flows.
- Use Binary Authorization for images built and signed by the approved pipeline.
- Apply BigQuery policy tags to personal-data columns and use customer-managed encryption keys with documented access and rotation procedures.

## 8. Observability and testing

- Measure request success rate and latency at the load balancer and alert on one-hour and six-hour error-budget burn rates.
- Dashboard per-zone capacity, scheduling, autoscaling, quotas, NAT capacity, database health, replica lag, backups, Datastream lag, slot/WAL growth, BigQuery freshness, and regional backend health.
- Run a zone-failure game day at least quarterly.
- Run a full regional-recovery rehearsal at least annually, including fencing, promotion, traffic switching, credentials, CDC recovery, rollback, and split-brain controls.

## 9. Build acceptance gates

Before production cluster creation, the platform lead must attach and approve:

1. The two-region node-pool matrix: minimum, normal, maximum, surge, per-zone counts, quotas, and reserved headroom.
2. The finalized Pod secondary-range calculation and expansion plan.
3. Load-test results proving 5,000 requests/second with retries and one-zone-loss headroom.
4. Read-replica and cross-region replica lag thresholds and measured results.
5. Datastream freshness, WAL/slot-growth, failover, and replay test results.
6. A timed regional-recovery rehearsal demonstrating fencing, lag verification, promotion, endpoint and credential cutover, Datastream recovery, global load-balancer convergence, rollback, and split-brain prevention.

For every gate, record the named owner, evidence link, measured or otherwise recorded value, pass/fail threshold, pass/fail status, and approval date. Representative or pre-production environments may be used for load and failure testing where documented and representative. Cluster creation is blocked until the IP-plan and quota gates pass. No production traffic is permitted until every applicable gate has recorded evidence, an owner, pass/fail status, and approval. If any gate lacks measured evidence, the affected production build or SLO is not approved; the document’s conditional RTO, RPO, capacity, and freshness objectives do not become guarantees by assertion.