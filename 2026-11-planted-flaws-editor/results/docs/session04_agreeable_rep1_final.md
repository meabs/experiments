# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets and availability

- Customer-facing stateless web and API service target: 99.95% monthly availability, with an error budget of approximately 22 minutes per month.
- The end-to-end SLO includes the load balancer, GKE workloads and dependencies, Cloud SQL, networking, and required Google Cloud APIs. Individual component targets do not automatically compose to a 99.95% platform target; the team will maintain an explicit dependency/error-budget model.
- The platform operates in three zones and must survive loss of one zone without operator intervention.
- Loss of the whole region is handled by a documented and rehearsed recovery in a second region, with a 15-minute RTO and a target RPO of 5 minutes, subject to the measured cross-region database replication lag.
- Peak traffic is approximately 5,000 requests per second. The team consists of eight engineers operating managed services.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled.
- The pod secondary range is sized for the maximum expected node count, autoscaler growth, and surge capacity. It is substantially larger than /22 (initially /18, subject to validation against the final maximum node count and GKE allocation behavior).
- The cluster is VPC-native with private nodes. Control-plane access is limited to authorized networks. Internet egress uses Cloud NAT through a regional Cloud Router.
- The cluster uses the Regular GKE release channel. A weekly maintenance window runs on Sunday from 02:00 to 06:00 local time.

## 3. Capacity

- Each API pod serves approximately 800 requests per second. Six replicas provide capacity above the 5,000-request-per-second peak with headroom.
- Each zone's node pool is sized for approximately 60% utilization at peak. After loss of one zone, the remaining zones carry the traffic at no more than the validated emergency utilization target, and the autoscaler adds nodes as required.
- Capacity tests validate pod, node, IP-range, quota, and load-balancer limits, including zonal loss and node-pool surge scenarios.

## 4. Workload placement and disruption

- Stateless tiers run six replicas, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Required hostname anti-affinity is used where the guarantee that replicas do not share a node is necessary; capacity and scheduling feasibility are validated before rollout.
- Each tier has a PodDisruptionBudget with `minAvailable: 5`, allowing controlled voluntary disruption while preserving service capacity.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`.
- Deployments and rollouts are configured and tested so that readiness checks, capacity, and disruption budgets preserve the availability SLO during normal changes.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region.
- Health checks use the application's `/healthz` endpoint, with connection draining set to 60 seconds.
- Regional failover uses the load balancer's configured health-based backend failover or traffic steering, not a 3,600-second DNS TTL. Failover behavior and detection time are tested as part of the recovery rehearsal.
- Recovery-region traffic is advertised only after an explicit readiness gate confirms that the database has been promoted and is writable, application connections and writes have been cut over and validated, and CDC freshness/replay validation has succeeded. Infrastructure or pod health alone is insufficient.
- The recovery runbook includes enabling or validating the secondary-region application, database promotion and connection cutover, write redirection, configuration changes, validation of CDC, the recovery readiness gate, and rollback or failback procedures.

## 6. Database

- The transactional database is Cloud SQL for PostgreSQL in europe-west2 with high availability enabled: a primary in one zone and a standby in another, with automatic intra-region failover. The HA standby is not used as a read endpoint.
- Analytics dashboards use a separately provisioned, supported Cloud SQL read replica. Its sizing, lag thresholds, monitoring, and behavior during primary or regional failover are documented; dashboards tolerate temporary unavailability or lag.
- Automated backups and point-in-time recovery are enabled.
- A cross-region read replica in europe-west1 is the target for regional recovery. The runbook promotes it, redirects application writes, and validates data and application behavior.
- The regional RPO is based on measured and alerted cross-region replication lag; recovery is permitted only within the documented maximum-lag/RPO criteria, or the incident is explicitly reported as an RPO exception.
- Backup restoration is size- and workload-dependent. The team defines measured restore objectives, tests restores regularly, and uses the tested result in the database recovery plan rather than assuming a fixed five-minute duration.

## 7. Change data capture to BigQuery

- Datastream uses a supported, low-impact Cloud SQL logical-decoding configuration to read committed changes from the primary and write them to BigQuery without endangering primary workload capacity.
- End-to-end CDC freshness target is five minutes, with alerts when replication lag or freshness reaches three minutes.
- The BigQuery destination's staleness limit is 15 minutes, subject to confirmation that this does not conflict with the five-minute freshness requirement.
- Change events are applied idempotently using a primary-key merge, so duplicate delivery does not create duplicate rows.
- The regional recovery runbook validates the CDC source, offsets, replay, deduplication, and destination freshness after promotion. These checks are prerequisites for advertising the recovery backend.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default.
- Binary Authorization admits only images built by the approved pipeline.
- Columns containing personal data are covered by policy tags in BigQuery, and datasets use customer-managed encryption keys.

## 9. Observability

- Service-level indicators are request success rate and latency measured at the load balancer.
- Alerts cover one-hour and six-hour error-budget burn rates, regional backend health, failover status, database replication and read-replica lag, CDC freshness, node-pool capacity by zone, IP and quota headroom, and autoscaler state.
- Dashboards show the measured RPO/RTO signals and recovery readiness, including database promotion, write cutover, and CDC validation status.

## 10. Testing and operations

- A zone-failure game day occurs quarterly.
- A full regional recovery rehearsal occurs annually and includes load-balancer failover, the recovery readiness gate, database promotion, application write cutover, CDC validation, and measured RTO/RPO.
- Backup restores, read-replica behavior, node upgrades, autoscaling, and capacity limits are tested on a schedule.
- Each exercise produces a written report with measured results, unresolved risks, and assigned follow-up actions.