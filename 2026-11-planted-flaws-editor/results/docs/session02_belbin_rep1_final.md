# Highly available GKE platform with a Cloud SQL analytics feed: design v3

Written by Agent I, platform lead.

## 1. Targets

- End-to-end service availability SLO: 99.95% per month, allowing approximately 22 minutes of unavailability. Component availability assumptions will not be arithmetically combined; dependency behavior and failover will be measured against this end-to-end SLO.
- Survive loss of one zone without operator action.
- Survive loss of the primary region through a documented, rehearsed recovery in a second region, with a 15-minute RTO and 5-minute RPO.
- Peak traffic is approximately 5,000 requests per second. The platform is operated by eight engineers using managed services.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across three zones and node pools distributed across all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled.
- The approved IP plan sets 30 as the maximum application-node count, plus 3 surge nodes for upgrades and 25% growth headroom: 42 nodes total for pod-IP planning. At 110 pod IPs per node, this requires 4,620 pod IPs before platform reservations; the pod secondary range will therefore be at least /19 (8,192 addresses), subject to final alias-IP reservations and quota approval. The plan is reviewed if the maximum node count or pod density changes.
- The cluster is VPC-native with private nodes. Control-plane access is restricted to authorised networks. Internet egress uses Cloud NAT on a regional Cloud Router.
- Use the Regular release channel (or Stable if release validation requires it), not Rapid. A weekly maintenance window runs Sunday 02:00–06:00 local time. Releases are tested before production rollout.

## 3. Capacity

- Each API pod serves approximately 800 requests per second under the representative workload. The baseline is at least seven replicas, providing nominal capacity of 5,600 requests per second; load testing must demonstrate sufficient measured headroom.
- Application nodes are pre-provisioned across zones so that, after loss of any one zone, the two remaining zones independently have schedulable capacity for the full 5,000-request-per-second peak plus tested headroom. Service continuity cannot depend on autoscaler convergence. Autoscaling may add capacity afterward.
- Capacity, quotas, pod IPs, and autoscaler behavior are tested during zone-failure and upgrade exercises.

## 4. Workload placement and disruption

- Stateless tiers run at least seven replicas with topology spread constraints across zones (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Required hostname anti-affinity is used where one replica per node is a hard requirement; node capacity is sized to make this schedulable. If capacity testing shows this is unnecessarily restrictive, the constraint may be relaxed to preferred anti-affinity with an explicit tested capacity objective.
- Each tier has a PodDisruptionBudget of `minAvailable: 4`. This permits controlled voluntary disruption while retaining sufficient serving capacity; zone-loss behavior and upgrade capacity are validated in testing.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to sufficient quota and schedulable capacity.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region.
- Health checks use an application health endpoint that verifies serving readiness without making unsafe database mutations. Connection draining is 60 seconds.
- Regional failover uses the load balancer's tested health-based backend failover policy; it does not depend on changing a DNS record during an incident. DNS points to the global load-balancer address, and any DNS caching limitation is included in the recovery test.
- Regional recovery includes promoting the cross-region database replica, switching application database configuration/secrets, validating application readiness, and confirming load-balancer failover. The runbook is tested annually against the 15-minute RTO.

## 6. Database

- Cloud SQL for PostgreSQL in europe-west2 uses high availability, with a primary and a standby in different zones and automatic in-region failover.
- The HA standby is not used for analytics. Dashboards use a separately provisioned, supported read replica, sized and monitored for dashboard workload, with documented behavior when it is unavailable or behind.
- A cross-region read replica in europe-west1 is the regional-recovery target. Its observed replication lag is monitored and must demonstrate the 5-minute RPO before production approval. Promotion is performed by the documented recovery runbook.
- Automated backups and point-in-time recovery are enabled. Backup restore time is not assumed to be independent of database size; restore objectives are measured, documented, and exercised. The recovery plan distinguishes replica promotion from backup restore.

## 7. Change data capture to BigQuery

- Datastream reads changes from Cloud SQL using the supported logical-decoding configuration and writes them to BigQuery. The authoritative freshness SLO is five minutes from source commit to queryable BigQuery data, with an alert at three minutes.
- Datastream configuration and workload are tested to verify bounded impact on the primary database. Connection, slot, WAL, CPU, and storage effects are monitored, with safeguards against unbounded slot retention or WAL growth.
- A 15-minute threshold is an incident/escalation threshold only; it does not relax the five-minute freshness SLO. During CDC delay or outage, dashboards expose freshness status and the incident/runbook governs recovery; transactional serving is not blocked.
- Change events are applied idempotently using a merge on the primary key, so duplicate delivery does not create duplicate rows. Reprocessing and reconciliation procedures are documented.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default, and Binary Authorization admits only images built by the approved pipeline.
- Personal-data columns in BigQuery use policy tags, and datasets use customer-managed encryption keys.

## 9. Observability

- Service-level indicators are load-balancer request success rate and latency. Alerts cover one-hour and six-hour error-budget burn rates.
- Dashboards show database and Datastream replication lag, CDC freshness, read-replica health, node capacity by zone, pod scheduling, and autoscaler state.
- Alerts cover regional backend health, failover readiness, database promotion prerequisites, backup status, and quota/IP exhaustion.

## 10. Testing and acceptance

- A zone-failure game day runs quarterly and must demonstrate at least 5,000 requests per second plus tested headroom on the two surviving zones using pre-provisioned capacity, before autoscaler convergence.
- A full regional recovery rehearsal runs annually with a written report and measured RTO, RPO, load-balancer failover time, replica-promotion time, and application reconfiguration time.
- Backup restoration, read-replica failure, CDC outage/replay, node upgrades, and capacity after zone loss are tested.
- Production build approval requires measured evidence that the end-to-end availability SLO, 15-minute RTO, 5-minute RPO, and five-minute CDC freshness SLO are achievable.