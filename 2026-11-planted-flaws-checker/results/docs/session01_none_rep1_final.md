# Highly available GKE platform with a Cloud SQL analytics feed: design v3

Written by Agent I, the platform lead.

## 1. Targets

- The platform SLO is 99.95% monthly availability for successful, timely customer requests, measured at the global load balancer. Dependency availability is treated as part of this end-to-end SLO; individual 99.95% component targets do not compose to 99.95%.
- The platform must survive loss of one zone without manual intervention.
- Loss of the whole region must be recoverable through a documented and rehearsed procedure in a second region, with a 15-minute RTO and a five-minute RPO target. The achievable RPO is governed by measured cross-region replication lag; any lag beyond the target is reported as potential data loss during promotion.
- Peak traffic is about 5,000 requests per second. The team consists of eight engineers operating managed services.

## 2. Cluster and node topology

- One regional GKE Standard cluster is deployed in `europe-west2`, with the control plane replicated across the region's three zones and node pools in all three zones.
- Separate system and application node pools use cluster autoscaling.
- The pod secondary range is enlarged from `/22` to at least `/18`, with the final size and maximum node count validated against GKE secondary-range allocation, surge capacity, and expected growth.
- The cluster is VPC-native with private nodes. Access to the control-plane endpoint is limited to authorised networks. Internet egress uses Cloud NAT on a regional Cloud Router.
- The cluster uses the Regular release channel (or Stable if all required features are supported), following compatibility testing. A weekly maintenance window runs Sunday 02:00–06:00 local time, with upgrades rehearsed and monitored.

## 3. Capacity

- Each API pod serves about 800 requests per second under representative load. The normal deployment uses at least seven replicas, providing more than the 5,000-request-per-second peak subject to load testing, resource limits, and tested headroom.
- Application capacity in the surviving zones is pre-sized for one-zone loss, including per-zone pod and node reservations, quotas, pod IPs, and surge capacity. Peak service must not depend on autoscaler startup after a zone failure.
- Capacity, quota, pod-range exhaustion, startup time, and autoscaler behavior are tested for normal operation, zone loss, and rolling upgrades. Tests cover peak traffic with the required headroom and uneven placement.

## 4. Workload placement and disruption

- Stateless tiers run at least seven replicas, spread across zones using topology spread constraints with `maxSkew: 1` and `whenUnsatisfiable: DoNotSchedule`.
- Preferred hostname anti-affinity discourages colocating replicas on one node; the resulting placement is verified in production configuration.
- Each tier uses a PodDisruptionBudget with an availability floor that permits controlled maintenance, initially `minAvailable: 5` for seven replicas. Capacity is verified so that voluntary disruption does not violate the service SLO.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to available quota and capacity.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use an application endpoint that verifies serving readiness without unnecessarily depending on the transactional database. Connection draining is 60 seconds.
- Regional failover uses the load balancer's health-based backend failover, not a 3,600-second DNS change. The second region has continuously deployable application capacity and tested configuration.
- Recovery is sequenced and acceptance-tested: fence the failed primary, verify cross-region replica lag and the RPO decision, promote and validate the database replica, reconfigure application database connections, reconfigure or restart Datastream, reconcile CDC state, and validate application readiness. The recovery-region backend remains disabled or unready and must not receive traffic until database promotion, application reconfiguration, CDC recovery, and readiness validation complete.
- The recovery runbook records timing against the 15-minute RTO and five-minute RPO targets. Health-based load-balancer failover is tested as part of the complete sequence.
- DNS, if used for any supplemental routing, has a low TTL and documented resolver/client limitations.

## 6. Database

- Cloud SQL for PostgreSQL runs in `europe-west2` with high availability enabled: a primary in one zone and a standby in another, with automatic regional failover. Automated backups and point-in-time recovery are enabled.
- The HA standby is not used for queries. Analytics dashboards use a separately provisioned, supported read replica (or an explicitly approved BigQuery path). Replica lag and query load are monitored so reporting cannot materially affect the primary.
- A cross-region read replica in `europe-west1` is the regional-recovery target. Its replication lag is continuously monitored and alerted against the five-minute RPO target. The runbook documents fencing, promotion, application connection changes, validation, and the possibility of losing transactions not yet replicated.
- Backup restore timing is not assumed to be independent of database size. Restore RTO is established through tests using a representative database and is included in the recovery plan; larger databases require measured capacity and timing.
- Migration procedures include backups, compatibility checks, rollback planning, and testing for destructive or corrupting changes.

## 7. Change data capture to BigQuery

- Datastream reads changes from the Cloud SQL primary through logical decoding and writes them to BigQuery. The target freshness is five minutes, with an alert at three minutes.
- Logical-replication slot health, WAL retention, storage growth, and Datastream lag are monitored. Retention thresholds and an operational response prevent CDC backlog from endangering primary storage or availability.
- During regional recovery, the runbook defines how Datastream is stopped, reconfigured, or restarted against the promoted database, including duplicate and missing-event handling and reconciliation. CDC recovery is validated before the recovery backend is enabled.
- BigQuery staleness and cost settings are documented and validated against the five-minute committed-change requirement; a 15-minute limit is not used if it violates that requirement.
- Change events are applied idempotently, using a merge on the primary key and suitable event ordering/version handling.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default. Binary Authorization admits only images built and attested by the approved pipeline.
- Personal-data columns are protected with BigQuery policy tags, and datasets use customer-managed encryption keys.

## 9. Observability

- SLIs are request success rate and latency measured at the load balancer. Alerts cover one-hour and six-hour error-budget burn rates.
- Dashboards and alerts cover Cloud SQL HA and cross-region replica lag, analytics-replica lag, Datastream freshness and slot/WAL retention, BigQuery freshness, node-pool capacity by zone, quotas, and autoscaler state.
- Recovery and failover events produce an audit trail, including observed RTO, RPO, replication lag, and data reconciliation results.

## 10. Testing and operations

- A zone-failure game day is conducted quarterly.
- A full regional recovery rehearsal is conducted at least annually, with a written report and tracked remediation.
- Load tests validate at least seven API replicas serving 5,000 requests per second with headroom, one-zone loss without relying on autoscaler startup, failover sequencing and backend gating, upgrade/drain behavior, pod-range and quota headroom, database replica promotion, restore timing, and CDC recovery without primary-storage exhaustion.
- Maintenance, GKE upgrades, database failover, replica promotion, Datastream reconfiguration, and rollback procedures are documented and owned.