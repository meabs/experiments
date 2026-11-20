# Highly available GKE platform with a Cloud SQL analytics feed: design v5

## 1. Targets and availability

- Customer-facing service target: 99.95% monthly availability, measured by successful requests and latency at the global load balancer.
- The design survives loss of one zone without operator action. Regional loss has a documented, rehearsed recovery with a 15-minute RTO and 5-minute RPO target.
- Regional RPO is bounded by monitored, observed cross-region replica lag; it is not assumed from configuration.
- Peak traffic is approximately 5,000 requests/second. The team consists of eight engineers using managed services.
- The 99.95% target is an end-to-end objective, not the result of multiplying or assigning identical availability figures to dependencies. Dependency budgets, alerting, and error-budget policy will be documented and reviewed.
- Recovery, failover, upgrades, and zone-loss capacity are validated with game days and measured results before production.

## 2. Cluster and node topology

- Use one regional GKE Standard cluster in `europe-west2`, with control plane replicated across three zones and node pools distributed across all three zones.
- Provision a warm-standby application environment in `europe-west1`, either as a separately managed GKE Standard cluster or another explicitly supported deployment. It has independently provisioned node capacity, pod IP ranges, quotas, synchronized deployment/configuration, monitoring, and global-load-balancer backend registration.
- The `europe-west1` standby maintains the minimum application and system capacity needed to become schedulable during recovery. Record and test minimum nodes, replica count, `maxPodsPerNode`, secondary ranges, quotas, autoscaler limits, and scale-up time. Validate readiness continuously or during documented controlled checks; an untested or unschedulable backend is not healthy.
- The standby is explicitly active/passive. While its database is read-only, its backend is excluded from normal serving traffic and its serving readiness condition is false. It may be health- or administratively monitored, but must not receive production requests. It becomes serving only after old-writer fencing, database promotion, application endpoint/configuration cutover, and write/read validation.
- Both clusters use separate system and application node pools, cluster autoscaling, explicit minimum/maximum sizes, private nodes, restricted control-plane access, and suitably sized monitored Cloud NAT.
- Use the Regular release channel, or Stable if it meets feature requirements, with a tested upgrade policy and weekly maintenance window.
- Size each pod secondary range from GKE’s configured per-node Pod CIDR allocation, maximum nodes, maximum pods per node, surge capacity, and growth headroom. A `/22` is insufficient; reserve and test a larger range, initially at least `/19`, adjusted from the actual allocation calculation.
- Capacity and quota tests must demonstrate that loss of any zone leaves sufficient capacity for required replicas and system pods with headroom. The standby-region test must demonstrate that required replicas become ready within the regional RTO.

## 3. Capacity and placement

- Do not claim that six replicas at approximately 800 requests/second exceed 5,000: that is only 4,800. Use at least eight replicas, or demonstrate materially higher per-replica capacity through load testing.
- Resource requests/limits, autoscaling thresholds, node capacity, quotas, and replica counts must provide headroom at peak, after zone loss, and during upgrades.
- Stateless tiers use at least eight replicas, or another load-tested count, with topology spread constraints across zones (`maxSkew: 1`, `DoNotSchedule`) and required hostname anti-affinity where one replica per node is required.
- Use an availability-compatible PDB, such as `minAvailable: 7` for eight replicas; do not require every replica. Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to demonstrated spare capacity.
- Validate zone-loss, burst, upgrade, autoscaler, quota, pending-pod, maximum-node, and IP-limit behavior in both regions. The standby must be load-tested at the required post-failover load, including its own zone-loss constraints.

## 4. Traffic and regional recovery

- Use a global external Application Load Balancer with active/passive regional backends. `europe-west2` is serving during normal operation. `europe-west1` is non-serving while its database is read-only, regardless of basic infrastructure health.
- Health checks use a dependency-light endpoint. The standby endpoint must not report serving readiness until promotion, application cutover, and validation complete. Connection draining is 60 seconds.
- Regional failover uses health-based backend failover, not a 3,600-second DNS update. Any DNS has documented TTL and resolver-cache assumptions compatible with the RTO.
- The recovery runbook fences the old writer before promotion, records replica lag, gates or qualifies promotion when observed lag exceeds five minutes, promotes the replica, changes application configuration, validates writes, re-establishes CDC, then changes standby readiness/backend state to serving.
- Recovery testing includes standby scheduling/readiness, active/passive routing, old-writer fencing, database promotion, application cutover, readiness transition, load-balancer convergence, CDC re-establishment, and validation that the old or unpromoted backend cannot receive traffic. The complete sequence must meet the measured 15-minute RTO.

## 5. Database and CDC

- Cloud SQL for PostgreSQL uses regional HA, automated backups, and point-in-time recovery. The HA standby is not used for queries.
- Analytics uses a separately provisioned supported read replica or extraction architecture, with capacity and lag monitored.
- A cross-region asynchronous read replica in `europe-west1` is the recovery target. Promotion is fenced and tested. The 5-minute RPO is an acceptance criterion bounded by observed lag; if lag exceeds five minutes, promotion is gated or explicitly qualified and resulting data loss/customer impact is recorded.
- Restore time is measured at representative database sizes; it is not assumed to be five minutes.
- Datastream uses a supported Cloud SQL PostgreSQL CDC configuration. Monitor logical-decoding overhead, replication slots, WAL retention, primary impact, lag, and backpressure. Handle inserts, updates, deletes, ordering, schema evolution, retries, replay, checkpoints, and poison events. BigQuery application is idempotent and tested beyond primary-key merge semantics.
- During recovery, Datastream is fenced from the old writer, then reconfigured against the promoted writer with checkpoint/replay validation. The target is committed-change freshness within five minutes, with alerts at three minutes and documented failure runbooks.

## 6. Security, observability, and testing

- Use Workload Identity Federation, one least-privilege service account per tier, default-deny network policies, Binary Authorization, BigQuery policy tags for personal data, customer-managed encryption keys, and tested key-access/rotation procedures.
- Monitor request success/latency, error-budget burn, backend and regional health, standby serving state, readiness and drift, capacity, quotas, autoscaling, database failover, replica lag, WAL retention, CDC freshness, and BigQuery apply failures.
- Runbooks cover zone loss, regional failover, database promotion, CDC pause/replay, bad migrations, quota exhaustion, and rollback.
- Conduct quarterly zone-failure game days and an annual full regional recovery rehearsal. Before production test peak load, zone loss, upgrades/drains, both-region autoscaling and quotas, database failover/promotion, restore, CDC correctness, active/passive routing, readiness transition, and load-balancer convergence.
- Production launch requires evidence meeting the 99.95% service objective, 15-minute regional RTO, 5-minute regional RPO when observed lag is within bound, and approximately five-minute CDC freshness under documented assumptions.