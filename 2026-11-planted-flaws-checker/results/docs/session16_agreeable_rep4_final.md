# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets

- End-to-end service availability target: 99.95% per month (approximately 22 minutes of downtime), measured at the global load balancer. The error budget covers the application, platform, database, networking, and operational dependencies; component availability figures are not assumed to compose arithmetically.
- Survive the loss of one zone without manual intervention.
- Survive the loss of the whole region through a documented and rehearsed recovery in a second region, with an RTO of 15 minutes and a target RPO of 5 minutes.
- Peak traffic is approximately 5,000 requests per second. The team is eight engineers operating managed services.

## 2. Cluster and node topology

- One regional GKE Standard cluster in `europe-west2`, with the control plane replicated across the region's three zones and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled. Autoscaler minimums, maximums, regional quota, and surge capacity are sized and tested for normal operation, zone loss, and upgrades.
- The cluster is VPC-native with private nodes. Size the pod secondary range for the maximum node count, 110 pods per node, upgrade surge, and growth headroom; use at least a `/20` and preferably `/19` where required by the documented calculation. Confirm the calculation against configured autoscaler limits before build.
- Access to the control-plane endpoint is limited to authorised networks. Internet egress uses Cloud NAT on a regional Cloud Router.
- Use the GKE Stable release channel for production, with a tested maintenance window on Sunday from 02:00 to 06:00 local time.

## 3. Capacity

- Size and load-test the API deployment so that its measured capacity exceeds 5,000 requests per second with operational headroom. Six replicas at an assumed 800 requests per second provide only 4,800 requests per second and are therefore insufficient as a design assumption; use at least seven replicas or a higher, measured per-pod capacity with documented headroom.
- Each zone's node pool is sized for approximately 60% utilisation at peak traffic. After loss of one zone, the remaining zones carry the traffic at no more than the tested capacity threshold, and the autoscaler adds nodes within its configured limits and available regional quota.
- Capacity, pod IPs, autoscaler behaviour, and scale-up time are load-tested for peak traffic, zone loss, and rolling upgrades.

## 4. Workload placement and disruption

- Stateless tiers run enough replicas to meet the capacity target, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Required hostname anti-affinity is used where one replica per node is a requirement; otherwise the placement guarantee and its trade-offs are documented explicitly.
- Each tier has a PodDisruptionBudget preserving serving capacity while allowing controlled maintenance, for example `minAvailable: 5` for six replicas or the equivalent tested floor for the chosen replica count. Capacity and surge headroom are verified before upgrades and drains.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with health-checked backends in both regions. The regional backends are configured for health-based failover; the application health endpoint is used only if it accurately represents serving readiness.
- Connection draining is 60 seconds. Regional failover and failback are tested, including health-check failure detection and propagation time.
- DNS is not used as the regional failover mechanism. Any service DNS record has a TTL compatible with normal address management, but the 15-minute RTO relies on load-balancer failover rather than DNS cache expiry.

## 6. Database

- The transactional database is Cloud SQL for PostgreSQL in `europe-west2` with high availability enabled: a primary in one zone and a standby in another, with automatic in-region failover. Automated backups and point-in-time recovery are enabled.
- The HA standby is not used for reads. Dashboards use a separate supported same-region Cloud SQL read replica (or another explicitly approved reporting path), with its lag, capacity, and failure behaviour monitored.
- A cross-region asynchronous read replica in `europe-west1` is the regional-recovery target. Its observed replication lag is monitored and must support the five-minute RPO under tested workload conditions.
- Regional recovery has a documented runbook covering promotion, application connection changes, load-balancer backend activation, validation, and later failback. Promotion is rehearsed at least annually.
- Backup restoration is not assumed to take a fixed time regardless of database size. Define a measured, size-dependent restore target, monitor backup health, and test restoration at a frequency sufficient to validate the target.

## 7. Change data capture to BigQuery

- Datastream reads changes from the Cloud SQL primary through supported logical decoding and writes them to BigQuery without imposing unsafe load on the primary. The committed-change freshness target is five minutes, and an alert fires at three minutes of CDC lag.
- Logical-decoding slot health, retained WAL volume, disk usage, and replication-slot age are monitored. Datastream pause/failure has bounded-WAL and back-pressure safeguards: alert and operationally pause or throttle ingestion before retention threatens primary capacity, with a documented recovery procedure.
- The BigQuery destination's 15-minute staleness limit applies to query-serving freshness and cost control; it does not relax the five-minute CDC delivery objective. User-facing documentation distinguishes the two, and freshness alerts and behavior are defined.
- Change events are applied idempotently using a merge on the primary key, so duplicate delivery does not create duplicate rows.
- The regional-recovery runbook documents Datastream handling: pause or reconfigure the source as appropriate after promotion, resume from a validated position, verify continuity and duplicate handling, and monitor lag. CDC recovery is tested against the five-minute RPO/freshness requirements.

## 8. Security

- Workloads reach Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default, and Binary Authorization admits only images built by the approved pipeline.
- Columns containing personal data are covered by policy tags in BigQuery, and datasets use customer-managed encryption keys.

## 9. Observability

- Service-level indicators are request success rate and latency measured at the load balancer. Alerting covers one-hour and six-hour error-budget burn rates.
- Dashboards show replication lag for the HA/read/cross-region replicas, CDC freshness, BigQuery staleness, logical-decoding slot/WAL retention, node-pool capacity per zone, autoscaler state, load-balancer backend health, and failover status.
- Alerts have documented ownership, escalation, and runbook links.

## 10. Testing

- Conduct a zone-failure game day every quarter and a full regional recovery rehearsal at least annually, each with a written report and tracked remediation.
- Test load capacity, rolling upgrades, pod disruption, Cloud SQL promotion, cross-region replica lag, backup restoration, load-balancer failover, Datastream pause/recovery and reconfiguration, slot/WAL safeguards, and duplicate handling. Demonstrate the stated RTO, RPO, CDC freshness, and measured restore target before production launch.