# Highly available GKE platform with a Cloud SQL analytics feed: design v2

## 1. Targets

- The end-to-end customer-facing availability SLO is 99.95% per calendar month, measured at the load balancer. Its error budget is approximately 22 minutes per month; dependency budgets and alerts are allocated within this overall budget rather than assuming that serial dependencies multiply to 99.95%.
- The platform must survive loss of one zone without operator action.
- Loss of the whole region is handled by a documented, rehearsed recovery in a second region, with an RTO of 15 minutes and an RPO of 5 minutes. These objectives are validated in recovery rehearsals.
- Peak traffic is about 5,000 requests per second. The team is eight engineers on a managed-service budget.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled and sufficient headroom for zonal loss.
- The pod secondary IP range is sized from GKE's per-node PodCIDR allocation, the maximum autoscaled node count, and growth headroom (not merely from the sum of nominal pod counts). The selected range and autoscaler maximum are recorded and validated to support the capacity plan; a /22 is not used for the stated 30-node/110-pods-per-node footprint.
- The cluster is VPC-native with private nodes. Access to the control plane endpoint is limited to authorised networks. Egress to the internet goes through Cloud NAT on a regional Cloud Router.
- The cluster uses the Regular (or Stable, if selected by the tested channel policy) release channel. Production upgrades are first validated in staging, and the maintenance window is validated against the chosen channel.

## 3. Capacity

- Each API pod can serve about 800 requests per second, so six replicas comfortably exceed the 5,000 requests-per-second peak; this estimate is verified by load testing.
- Each zone's node pool is sized to run at about 60% utilisation at peak traffic. After loss of one zone, the two remaining zones carry the traffic at about 90% initially, and the autoscaler adds nodes within the documented limits. Capacity and IP headroom are tested during a zone-failure game day.

## 4. Workload placement and disruption

- Stateless tiers run six replicas, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Required hostname anti-affinity is used where the design requires replicas not to share a node; scheduling capacity and autoscaler limits are validated so this does not prevent recovery.
- Each tier has a PodDisruptionBudget that permits maintenance while preserving the calculated serving minimum (initially `minAvailable: 5` for six replicas, subject to load and failure testing). It is not set to 6 of 6.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, and upgrade/drain behavior is tested.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use the application's `/healthz` endpoint, and connection draining is 60 seconds.
- The global load balancer performs health-based regional failover; regional recovery does not depend on changing DNS records. Any DNS used for service naming has a documented TTL and resolver-cache behavior, but it is not relied upon for the 15-minute failover objective.
- The recovery runbook covers application rollout/validation in the second region, database promotion and fencing, connection switching, and verification of health and replication state.

## 6. Database

- The transactional database is Cloud SQL for PostgreSQL in europe-west2 with high availability enabled: a primary in one zone and a standby in another, with automatic in-region failover. Automated backups and point-in-time recovery are enabled.
- The HA standby is not used as a read endpoint. Reporting uses a separately configured, supported Cloud SQL read replica (or an explicitly approved separate analytics path), sized for dashboard load and monitored for capacity, errors, and lag.
- A cross-region read replica in europe-west1 is the regional-recovery target. Its lag is continuously monitored and alerted, and the recovery runbook verifies replication state, promotes it, fences the old primary, and switches application connections. Rehearsals demonstrate the 5-minute RPO and 15-minute RTO.
- A bad migration is handled using point-in-time recovery or backup restore as appropriate. Restore time is explicitly size-dependent and based on measured recovery tests; no fixed five-minute restore guarantee is assumed. The measured objective and resulting RTO/RPO are recorded and retested.

## 7. Change data capture to BigQuery

- Datastream reads changes from the Cloud SQL primary through a supported logical-decoding configuration and writes them to BigQuery without an unsupported or untested primary workload.
- The logical-decoding replication slot and WAL-retention limits are documented and monitored, with alerts before retained WAL risks exhausting storage. Datastream replay, checkpointing, and duplicate delivery semantics are documented and tested, including behavior during Cloud SQL failover and recovery of the CDC stream.
- Target freshness is five minutes, with an alert at three minutes of replication lag. Primary CPU, I/O, lock impact, and CDC lag are load-tested at peak and during failover.
- The BigQuery destination's data staleness limit is 15 minutes to control query costs. Each change has a durable event/change identifier, and replay is idempotent using that identifier. Merge/update semantics preserve update history where required; row primary keys are used for entity state, not as the sole deduplication key.

## 8. Security

- Workloads reach Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default, and Binary Authorization admits only images built by the pipeline.
- Columns holding personal data are covered by policy tags in BigQuery, and datasets use customer-managed encryption keys.

## 9. Observability

- Service level indicators are request success rate and latency measured at the load balancer. Alerts cover end-to-end error-budget burn over one-hour and six-hour windows.
- Dashboards show regional backend health, replication lag, CDC freshness, read-replica capacity, node-pool capacity per zone, and autoscaler state.
- Alerts cover cross-region replica lag against the 5-minute RPO, CDC lag against the 5-minute freshness target, replication-slot/WAL retention before exhaustion, and failed or delayed failover or CDC recovery actions.

## 10. Testing and operations

- A zone-failure game day is run every quarter, including capacity, scheduling, load-balancer health failover, and database behavior.
- A full regional recovery rehearsal is run every year, including promotion, fencing, connection switching, measured RTO/RPO, and CDC behavior; each exercise has a written report and tracked remediation.
- Upgrade, restore, CDC-load and failover/replay, and read-replica capacity tests are run before production changes and after material topology or workload changes.