# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets and assumptions

- Customer-facing stateless web and API service availability SLO is 99.95% per calendar month, with an error budget of approximately 22 minutes.
- The platform is designed to survive loss of one zone without operator intervention.
- Loss of the whole primary region is recovered in a second region using a documented and rehearsed procedure, with an RTO of 15 minutes and a target RPO of 5 minutes.
- Peak traffic is approximately 5,000 requests per second. The team consists of eight engineers and uses managed services wherever practical.
- The end-to-end SLO is validated through load-balancer probes, application SLIs, database availability, dependency monitoring, and failover tests. Individual service availability figures are not multiplied or treated as proof of the end-to-end SLO.
- The SLO depends on healthy application capacity, Cloud SQL availability, load-balancer health-based routing, quota, IAM, networking, and tested failover procedures. These dependencies have owners, alerts, and error-budget actions.

## 2. Cluster and node topology

- One regional GKE Standard cluster is deployed in `europe-west2`, with the control plane replicated across the region's three zones and node pools distributed across all three zones.
- Separate system and application node pools use cluster autoscaling.
- The cluster uses a VPC-native network with private nodes. The pod secondary range is sized for the maximum approved node count, GKE allocation granularity, and growth headroom; the initial allocation is `/20` rather than `/22`, and capacity and quota are reviewed before increasing the node limit.
- Control-plane access is limited to authorised networks.
- Internet egress uses Cloud NAT on a regional Cloud Router.
- The cluster uses the Regular release channel. Upgrades follow a defined maintenance policy, with release validation, surge capacity, monitoring, and rollback or pause procedures. The weekly maintenance window is Sunday 02:00–06:00 local time.

## 3. Capacity

- Each API pod serves approximately 800 requests per second under the agreed workload. Six replicas are insufficient by themselves because they provide only approximately 4,800 requests per second before any failure. The API tier therefore uses an HPA with a production minimum of at least eight replicas and a maximum sized from load tests and node capacity; the exact maximum is recorded in the capacity plan and adjusted before planned peaks.
- Capacity tests include realistic CPU, memory, connection, and dependency limits rather than relying only on request rate. Tests establish the sustainable per-pod and per-zone capacity, including startup and autoscaler scale-up time.
- The capacity plan and zone-failure test demonstrate that the two surviving zones can sustain at least 5,000 requests per second at the required latency, with the agreed headroom and no more than 70% utilisation at peak after loss of one zone. This validation uses the HPA minimum and maximum, tested per-zone node capacity, quota, scheduling constraints, and autoscaler behaviour; it is not based solely on nominal replica count.
- Each zone is provisioned and autoscaled with sufficient quota and headroom that the remaining two zones can carry peak traffic after loss of one zone. Autoscaler scale-up time, pending pods, HPA saturation, and insufficient-capacity conditions are tested and alerted.
- Node-pool maximums, regional quotas, IP capacity, and PodDisruptionBudgets are checked as part of capacity reviews.

## 4. Workload placement and disruption

- Stateless tiers run at least eight replicas at normal production minimum, distributed across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Required pod anti-affinity on the hostname topology key prevents replicas of the same tier from sharing a node where the capacity plan supports that constraint.
- Each tier has a PodDisruptionBudget that preserves service capacity while permitting voluntary maintenance; the initial policy is `minAvailable: 5` for the API tier. The policy is validated during node drains and zone-loss tests and adjusted if the workload's availability requirements require it.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to quota and available IP capacity.
- Readiness, startup, and termination handling are configured so that traffic is removed before shutdown and replacement capacity becomes ready before disruption.

## 5. Traffic and regional failover

- Traffic enters through a global external Application Load Balancer with a backend service in each region.
- Health checks use an independent, correctly scoped application health endpoint and verify the dependencies necessary to serve traffic.
- Regional routing and failover are health-based and configured so an unhealthy primary-region backend is automatically removed and the secondary region receives traffic. This behavior is tested during regional recovery rehearsals.
- Connection draining is 60 seconds.
- DNS is not used as the regional failover mechanism. Any DNS records used for discovery have a TTL and propagation behavior that are separately tested and are not relied on to meet the 15-minute RTO.
- The secondary region has a prepared GKE deployment, quotas, secrets, images, configuration, and database connectivity sufficient to accept production traffic.

## 6. Database

- Cloud SQL for PostgreSQL is deployed in `europe-west2` with regional high availability enabled: a primary in one zone and a standby in another, with automatic intra-region failover.
- The HA standby is not used for reads. Analytics dashboards use a separately provisioned Cloud SQL read replica or another explicitly supported analytics path.
- Automated backups and point-in-time recovery are enabled and regularly validated.
- A cross-region asynchronous read replica in `europe-west1` is the regional-recovery target. Its measured replication lag is monitored continuously, with alerts and escalation when the measured lag threatens the five-minute RPO.
- Because cross-region replication is asynchronous, a five-minute RPO is a tested operational target rather than an unconditional guarantee. The recovery runbook records the last confirmed replicated position, stops or fences writers, promotes the replica, validates data consistency, and updates application connection configuration.
- Promotion prerequisites include replica health, acceptable measured lag, credentials and networking, schema compatibility, application configuration, and a verified write-fencing procedure to prevent split-brain.
- Restore and PITR are performed through a documented procedure. Recovery time is measured for the actual database size and workload; the five-minute restore assumption is removed. Restore drills include integrity checks, application validation, and recovery of CDC.

## 7. Change data capture to BigQuery

- Datastream reads Cloud SQL changes through the supported PostgreSQL logical-decoding configuration and writes them to BigQuery without placing query load on the primary.
- Replication slots, WAL retention, disk usage, failover behavior, and Datastream connectivity are monitored. Slot management prevents unbounded WAL growth.
- The target freshness SLO is five minutes. Alerts fire before the SLO is breached, including at three minutes, and escalation covers both CDC lag and destination errors.
- The BigQuery freshness/staleness policy is aligned with the five-minute requirement; a 15-minute staleness limit is not used as a substitute for the five-minute freshness target.
- Change events are applied idempotently using primary-key merge semantics and tracked source positions, so retries do not create duplicate rows.
- The CDC runbook covers Cloud SQL primary failover, logical-decoding reconnection, slot/WAL validation, regional promotion, replay or backfill, and verification that committed changes are delivered to BigQuery.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default.
- Binary Authorization admits only images built and signed by the approved pipeline.
- Columns containing personal data are protected with BigQuery policy tags, and datasets use customer-managed encryption keys.
- Secrets, keys, IAM bindings, and cross-region configuration are replicated or reproducibly provisioned for regional recovery.

## 9. Observability

- Service-level indicators are request success rate and latency measured at the load balancer and corroborated by application metrics.
- Alerts cover one-hour and six-hour error-budget burn, regional backend health, pending pods, HPA saturation, node and quota capacity per zone, autoscaler state, Cloud SQL failover and replica lag, WAL/slot retention, CDC freshness, and BigQuery ingestion errors.
- Dashboards show the last confirmed cross-region database position, recovery readiness, and the age of the most recent successful backup and restore validation.
- Alerts have documented owners, escalation paths, and runbooks.

## 10. Testing and operations

- A zone-failure game day is performed quarterly, including traffic redistribution, scheduling, autoscaling, HPA behaviour, database connectivity, and PDB behavior. Acceptance criteria include sustaining at least 5,000 requests per second on the two surviving zones at the required latency and within the capacity-headroom target.
- A full regional recovery rehearsal is performed at least annually and verifies the 15-minute RTO, measured database RPO, load-balancer failover, write fencing, replica promotion, application readiness, and CDC recovery.
- Backup restore and PITR tests are performed regularly, with measured recovery times recorded against the database-size and RTO assumptions.
- Capacity, quotas, IP ranges, release upgrades, and runbooks are reviewed before production launch and after material changes.