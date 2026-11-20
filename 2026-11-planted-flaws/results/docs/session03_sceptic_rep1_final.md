# Highly available GKE platform with a Cloud SQL analytics feed: design v4

## 1. Targets and assumptions

- Customer-facing stateless web/API service for users in one continent; peak traffic is approximately 5,000 requests/second.
- End-to-end monthly availability SLO is 99.95%. Dependency and maintenance budgets will be tracked against it.
- Primary region is `europe-west2`; the platform tolerates loss of one zone without operator action.
- Regional loss has a rehearsed recovery with RTO 15 minutes and RPO 5 minutes. These are measured targets, not service assumptions.
- The team has eight engineers and prefers managed services and automated runbooks.

## 2. Cluster and node topology

- Use one regional GKE Standard cluster in `europe-west2`, with control plane replication across three zones and node pools spread across all zones.
- Use separate system and application node pools with cluster autoscaling. Define minimum, maximum, and surge capacity per zone and test capacity after loss of a zone.
- The stated maximum of 30 nodes includes upgrade surge, failover capacity, and planned temporary growth. If the actual capacity plan exceeds 30, size all ranges and quotas for that larger maximum.
- Use VPC-native private nodes, restricted control-plane access, and monitored Cloud NAT sized for peak and failover traffic.
- Use the Stable GKE release channel unless a required feature is unavailable; pin and test upgrade versions and define maintenance and emergency-upgrade procedures.
- Size the pod secondary range from the configured GKE per-node pod CIDR allocation, maximum nodes including surge and growth, and headroom—not from current nodes. For the current maximum of 30 nodes at up to 110 pods per node, reserve at least `/19` under the common allocation model, subject to confirmation of the selected IP-alias configuration, and reserve additional expansion space where feasible.
- Monitor pod-IP and node capacity and alert before either becomes a scheduling constraint.

## 3. Capacity

- Benchmark representative workloads. The initial target is six replicas if testing confirms approximately 800 requests/second per pod, but autoscaling thresholds and headroom are based on measured CPU, memory, latency, and downstream capacity.
- Maintain sufficient capacity in every zone for peak traffic and sufficient spare capacity in two surviving zones after zone loss. Validate this with load and zone-failure tests, including autoscaler reaction time and pod startup time.
- Configure horizontal and cluster autoscaling with limits meeting failure and traffic-ramp objectives. Load-test peak traffic and regional recovery.

## 4. Workload placement and disruption

- Run at least six replicas for each stateless tier, distributed across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Use required or preferred anti-affinity as appropriate, and verify constraints do not prevent rescheduling during zone failure.
- Initially use a PDB of `minAvailable: 5` for a six-replica tier. Revisit after load testing; do not use `6 of 6` as routine upgrade policy.
- Use surge upgrades with `maxUnavailable: 0` where capacity permits, reserve node and IP headroom, and abort upgrades that threaten the SLO.

## 5. Traffic and regional recovery

- Terminate traffic on a global external Application Load Balancer with healthy backends in primary and recovery regions. Configure and test explicit health-based regional failover.
- Health checks represent serving readiness and include required dependencies without allowing transient analytics failure to remove the web service.
- The recovery runbook executes this ordered sequence:
  1. Declare regional failure and fence the old region: disable its write path and credentials/endpoints, block writes at the database/network layer where feasible, and verify that the old application cannot resume writes.
  2. Check cross-region replica lag, record the measured potential data-loss window, and validate replica health and promotion eligibility. If lag exceeds five minutes, page the owner, keep the old region fenced, and halt or restrict writes while waiting for lag recovery. Proceed with promotion only after lag is acceptable or an explicitly authorized larger loss window is accepted and recorded.
  3. Promote the recovery Cloud SQL replica and validate promotion state, schema, and application connectivity.
  4. Reconfigure the recovery application to the promoted database endpoint, validate reads and writes, and reconcile any in-flight or unreplicated commits. Possible loss is documented as up to the measured RPO, or the explicitly accepted larger window.
  5. Re-establish Datastream from the promoted source, recover its checkpoint/slot state, and run duplicate-safe reconciliation for the affected interval.
  6. Validate the service, CDC freshness, and data integrity, then enable writes and shift load-balancer traffic. Rollback is permitted only while fencing prevents split brain.
- Connection draining is 60 seconds unless testing requires another value. DNS is not relied on for the 15-minute RTO; auxiliary DNS has a verified low TTL and documented resolver limitations.

## 6. Database

- Use Cloud SQL for PostgreSQL regional HA: primary and managed standby in different zones, with automatic same-region failover. The HA standby is not a reporting endpoint.
- Use a separately provisioned supported read replica (or explicitly approved BigQuery-serving path) for analytics, with defined size, connection limits, lag SLO, and failure behavior. Dashboards degrade or use stale data if unavailable and never overload the primary.
- Maintain a cross-region read replica in `europe-west1`. Continuously monitor lag and WAL retention, alert against the five-minute RPO, and measure promotion and endpoint-switching time in rehearsals.
- Automated backups and PITR are enabled. Corruption recovery uses a tested, size-dependent restore procedure recording restore duration, achievable RPO, validation, and replay/reapplication effects.

## 7. Change data capture to BigQuery

- Configure Datastream using supported Cloud SQL PostgreSQL logical decoding. Verify flags, slots, permissions, failover behavior, and slot/WAL monitoring.
- The committed-change freshness target is five minutes; alert at three minutes. Bound WAL retention and define controlled pause/resume, checkpoint recovery, resynchronization, and post-promotion reconciliation.
- Use durable event identity such as source transaction/LSN plus relation/key information; a row primary key alone is insufficient.
- Define BigQuery freshness alerts, degraded behavior, and reconciliation. Validate end-to-end freshness, duplicates, ordering, schema changes, outages, promotion, and recovery under load.

## 8. Security

- Use Workload Identity Federation with one least-privilege service account per tier and no exported keys.
- Deny cross-namespace traffic by default, use NetworkPolicy, and admit only attested images through Binary Authorization.
- Apply BigQuery policy tags to personal-data columns and use customer-managed encryption keys with tested access and rotation.
- Store credentials and secrets in a managed secret store with rotation and audit logging.

## 9. Observability and operations

- Measure load-balancer and application success rate and latency. Alert on one-hour and six-hour error-budget burn, saturation, dependency failures, database lag, replica promotion state, Datastream lag/WAL retention, and BigQuery freshness.
- Dashboard pod IPs, node capacity by zone, autoscaler state, NAT capacity, and load-balancer health.
- Define owners, paging thresholds, and executable runbooks for zone loss, regional recovery and fencing, database failover, CDC backlog/promotion recovery, and exhausted IP/capacity.

## 10. Testing and acceptance

Before production, execute load, pod/node/zone-loss, upgrade, database-failover, read-replica-failure, CDC-backlog, and regional-recovery tests. Regional rehearsal must demonstrate old-primary fencing, the lag-exceeded degraded mode, replica-lag and promotion validation, in-flight/unreplicated commit handling, endpoint switching, measured RPO/RTO, Datastream checkpoint/slot recovery, reconciliation, and BigQuery freshness. Conduct quarterly zone-failure game days and at least annual regional rehearsals. Build approval requires recorded measurements supporting the stated targets and executable runbooks.