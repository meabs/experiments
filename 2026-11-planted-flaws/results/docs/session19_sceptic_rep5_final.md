# Highly available GKE platform with Cloud SQL analytics feed: design v3

## 1. Targets and acceptance criteria

- End-to-end customer availability SLO is 99.95% per calendar month, measured at the global load balancer for successful, correctly authorized responses completed within 500 ms at the 99th percentile. This measurement includes GKE, Cloud SQL, load balancing, networking, and required service dependencies. DNS resolver and client-side failures are not observable at this point; they are measured separately with synthetic probes and reported, but are not silently attributed to the load-balancer SLO. The error budget is approximately 22 minutes per month.
- The platform must continue serving through loss of one zone without operator intervention.
- Regional recovery has a 15-minute measured RTO and 5-minute measured RPO. These are acceptance criteria, not assumptions; they must be demonstrated in rehearsals using production-sized data and capacity.
- Peak load is approximately 5,000 requests/second. Capacity tests must include peak load, one-zone loss, rolling upgrades, and regional recovery.
- Every committed database change must reach BigQuery within five minutes, measured end to end from commit time to queryable destination data. This is a CDC freshness SLO, separate from customer availability.

## 2. GKE clusters and IP capacity

- The primary serving platform is one regional GKE Standard cluster in europe-west2, with private nodes and control-plane access restricted to authorized networks. It has node pools in all three zones, with separate system and application pools.
- For the 15-minute regional recovery target, a second, pre-provisioned warm-standby GKE Standard cluster is maintained in the designated recovery region. It has tested quotas, node pools, regional networking, Pod and Service secondary ranges, autoscaler limits, required images, configuration, secrets, IAM bindings, policies, and a registered global-load-balancer backend. Capacity is sufficient for the tested recovery load; building a new cluster, requesting quota, or allocating production IP ranges during the incident is not credited toward the RTO.
- Both clusters use the Regular release channel (Stable may be selected if all required features are supported), after compatibility testing. Define tested maintenance windows and upgrade rollback procedures; channel selection is not itself an availability guarantee.
- Configure Cloud NAT with regional redundancy as supported by the selected architecture, and monitor NAT port and error exhaustion.
- Pod and Service secondary ranges will be calculated separately for each cluster from the selected GKE IP-allocation mode, maximum autoscaled nodes, per-node Pod CIDR allocation, system pods, surge nodes, upgrades, and documented growth headroom. A /22 or assumed /19 is not accepted by default.
- The calculation and reservation, including maximum node count, standby capacity, quotas, and IP-utilization alarms, must be recorded before cluster creation. Exhaustion must be tested during autoscaling and surge upgrades.

## 3. Capacity and placement

- Run at least six API replicas across zones. Capacity tests must establish actual requests/second per pod, resource requests/limits, and node headroom.
- Surviving zones must have tested spare capacity, quotas, IP space, and autoscaler limits to absorb one-zone traffic without operator action. “90% utilization and then autoscale” is not sufficient unless demonstrated in a zone-failure test.
- Use topology spread constraints across zones. Use required hostname anti-affinity only where the resulting capacity and scheduling behavior have been tested; otherwise explicitly document that hostname separation is best effort.
- PodDisruptionBudgets must preserve the tested minimum serving capacity while permitting voluntary drains. A six-replica tier must not use `minAvailable: 6` if that blocks upgrades. Node-pool upgrades use surge capacity and a documented drain timeout; upgrade tests must verify that the PDB, scheduler, autoscaler, and quotas do not deadlock.
- Readiness checks must remove pods that cannot serve, and load-balancer health checks must test application readiness rather than merely process liveness.

## 4. Traffic and regional recovery

- Use a global external Application Load Balancer with independently health-checked regional backends for the primary and warm-standby clusters. Configure and test explicit health-based regional failover, including health thresholds, consecutive failures, draining behavior, timeout, propagation time, and behavior when all backends in a region fail. The load balancer, rather than a 3,600-second DNS update, is the normal traffic failover mechanism.
- `/healthz` must represent readiness to serve the application, including required database connectivity where appropriate, without unsafe or expensive database operations.
- The recovery runbook must detect and declare regional failure; promote the Cloud SQL cross-region replica; update the stable application database endpoint/configuration and secrets in the standby cluster; validate read/write behavior and migrations; validate and re-establish CDC; then enable or expose the recovered-region backend and validate traffic and error rates.
- The standby cluster’s images, configuration, secrets, IAM, network paths, quotas, node capacity, and load-balancer registration are maintained and periodically tested before an outage.
- If DNS is used for any control-plane or client endpoint, its TTL and resolver-cache behavior must be tested against the 15-minute RTO. DNS TTL alone is not credited as meeting the RTO.
- Regional recovery is rehearsed at least annually and after material architecture changes. The rehearsal records measured traffic restoration time, standby readiness, database promotion time, connection-switch time, data loss, and CDC recovery time.

## 5. Cloud SQL

- Use Cloud SQL for PostgreSQL with regional HA enabled for zonal failure. The HA standby is not a reporting endpoint.
- Dashboards use a separately provisioned, supported Cloud SQL read replica. Its capacity, replication lag, failure behavior, and fallback behavior are monitored and documented. Dashboards must not overload the primary or HA failover path.
- Use a cross-region read replica for regional recovery. Its replication lag is continuously monitored, and the recovery runbook has a promotion gate. If lag exceeds five minutes, the actual RPO is reported and the runbook records the resulting data-loss risk rather than claiming a five-minute RPO.
- Automated backups and point-in-time recovery remain enabled. Restore duration is measured against production-sized databases and realistic parallel load; there is no unconditional five-minute restore claim. Backup restore is a separately tested recovery option with a documented RTO.
- Application connections use a stable, switchable endpoint or configuration mechanism. Promotion, credential handling, connection draining, and stale connection invalidation are tested.

## 6. CDC and BigQuery

- Datastream is configured only after verifying supported Cloud SQL PostgreSQL logical-decoding prerequisites, required flags, permissions, and replication-slot behavior.
- Monitor source-to-destination freshness, Datastream lag, replication-slot retained WAL, disk growth, errors, throughput, and BigQuery apply delay. Alerts fire before WAL or freshness threatens the primary. Define hard operational thresholds and a procedure to pause or reconfigure CDC safely if the slot causes excessive WAL retention.
- The five-minute objective is measured from a database commit timestamp through arrival and successful application in BigQuery. A destination staleness setting is not a substitute for this SLO.
- Events carry stable source identity, transaction/ordering metadata, and operation type. Destination apply is idempotent and explicitly handles inserts, updates, deletes, retries, duplicates, out-of-order delivery, and replay.
- During regional recovery, Datastream is re-pointed or re-established according to a tested procedure. The procedure records the last safely applied position, prevents silent gaps, and permits controlled replay with deduplication. CDC continuity and freshness are verified before recovery is declared complete.

## 7. Security and observability

- Use Workload Identity Federation for GKE, one least-privilege Google service account per tier, no exported keys, default-deny namespace network policies, and Binary Authorization for pipeline-built images.
- Protect personal-data columns with BigQuery policy tags and use customer-managed encryption keys with tested key-access recovery.
- Monitor end-to-end availability and latency, synthetic DNS/client availability, error-budget burn, regional backend health, database failovers, replica lag, backup status, CDC freshness, slot/WAL retention, BigQuery apply errors, node capacity per zone, autoscaler state, NAT capacity, IP-range utilization, standby-cluster readiness, quotas, and load-balancer propagation.
- Alerts include one-hour and six-hour error-budget burn, CDC freshness approaching five minutes, and replica lag approaching the measured RPO limit.

## 8. Testing and approval gates

Before production build approval, the team must complete and retain evidence for:

1. IP, quota, and standby-capacity calculations covering maximum nodes, surge, system pods, and growth.
2. Peak-load, one-zone-loss, autoscaling, and rolling-upgrade tests.
3. Global load-balancer health-based regional failover tests, including measured propagation and draining behavior.
4. Cloud SQL promotion, endpoint switching, connection recovery, and measured RPO/RTO tests.
5. Backup/PITR restore tests at production-sized data volume.
6. Datastream logical-decoding, WAL-protection, failover, replay, duplicate, delete, and out-of-order tests.
7. End-to-end 99.95% availability and 500 ms p99 latency measurement plans, including separate DNS/client synthetic measurements and dependency budgets.
8. End-to-end five-minute CDC freshness measurement and recovery-region readiness tests.

Quarterly zone-failure game days and annual full regional recovery rehearsals continue, with written reports and corrective actions.