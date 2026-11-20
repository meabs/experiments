# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets and assumptions

- Customer-facing stateless web and API tiers serve users in one continent.
- Peak traffic is approximately 5,000 requests per second. The team consists of eight engineers using managed services.
- The monthly service availability target is 99.95%, with an approximately 22-minute monthly error budget.
- Availability is validated with an explicit dependency model and allocated error budgets for GKE, Cloud SQL, load balancing, networking, and other critical dependencies; it is not inferred by assigning each service the same availability target.
- The platform operates without intervention through loss of one zone.
- Loss of the whole region is handled by a documented and rehearsed recovery in a second region, with an RTO of 15 minutes and an RPO of 5 minutes.

## 2. Cluster and node topology

- One regional GKE Standard cluster is deployed in europe-west2, with the control plane replicated across the region's three zones and node pools in all three zones.
- Separate system and application node pools use the cluster autoscaler.
- The VPC-native pod secondary range is sized from the actual GKE alias-IP allocation rules for the configured maximum node-pool size, maximum pods per node, surge nodes, autoscaling headroom, and future growth. Capacity validation is completed before production.
- The cluster uses private nodes. Control-plane access is limited to authorised networks. Internet egress uses Cloud NAT on a regional Cloud Router, with NAT capacity sized and monitored for peak and failure scenarios.
- The cluster uses the Regular release channel (or Stable if required by the validated upgrade policy), not Rapid. A weekly maintenance window runs Sunday 02:00–06:00 local time, and upgrades are tested before production rollout.

## 3. Capacity

- Each API pod serves approximately 800 requests per second under representative load tests; six replicas therefore exceed the 5,000-request-per-second peak with appropriate headroom.
- Each zone's node pool is sized for approximately 60% utilisation at peak traffic. After loss of one zone, the remaining zones must be able to carry the load within tested capacity limits; autoscaling adds nodes subject to quota, IP-range, and regional capacity limits.
- Load, zone-loss, autoscaling, and node-upgrade tests validate these assumptions.

## 4. Workload placement and disruption

- Stateless tiers run six replicas spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Preferred hostname anti-affinity reduces replica co-location; capacity and topology constraints are the availability controls, rather than a guarantee that co-location can never occur.
- Each tier has a PodDisruptionBudget with `minAvailable: 5` for six replicas, allowing a voluntary eviction while preserving service capacity. This is reviewed against measured load and failover capacity.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to sufficient tested spare capacity.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a deployed, capacity-tested backend in each region. Health checks use the application's `/healthz` endpoint, and connection draining is 60 seconds.
- Regional failover uses the load balancer's health-based backend failover. Health checks and failover behavior are tested during regional recovery rehearsals.
- The regional recovery runbook is timed end to end: detect and declare the incident; promote the cross-region Cloud SQL replica; switch application configuration, credentials, and secrets; enable and validate the recovery-region application and load-balancer backend; verify database, application, and backend health/readiness; then allow health-based load-balancer failover. The recorded sum of these steps, including validation, must be no more than 15 minutes, and traffic is not failed over until the promoted database and recovery backend pass readiness checks.
- Promotion is permitted only when measured replica lag is within the 5-minute RPO requirement. Each rehearsal records the duration of every step and demonstrates the total RTO.
- Any DNS used for the service has a TTL and operational process compatible with the 15-minute RTO; DNS alone is not assumed to overcome resolver caching. The documented cutover includes routing, application configuration, credentials, and database endpoint changes.

## 6. Database

- Cloud SQL for PostgreSQL runs in europe-west2 with HA enabled: a primary in one zone and a standby in another, with automatic in-region failover. Automated backups and point-in-time recovery are enabled.
- The HA standby is not used as a read endpoint. Analytics dashboards use a separately supported Cloud SQL read replica or another explicitly supported analytics path. Its expected lag, monitoring, failure behavior, and fallback are documented.
- A cross-region read replica in europe-west1 is the regional-recovery target. Its observed replication lag is monitored and must support the 5-minute RPO. Promotion is performed through a documented, tested runbook that includes application and configuration cutover.
- Recovery and point-in-time restore duration is database-size- and workload-dependent. Restore, promotion, and cutover times are measured in rehearsals and must meet the stated RTO/RPO.

## 7. Change data capture to BigQuery

- Datastream reads changes from Cloud SQL using a validated, supported logical-decoding configuration and a dedicated logical replication slot, and writes them to BigQuery. The configuration is tested for throughput, slot/WAL retention, lag, failover behavior, and impact on the primary database.
- The target freshness is five minutes, with an alert at three minutes. Backlog, slot, WAL-retention, and primary-storage safeguards prevent CDC lag or an analytics outage from endangering the primary.
- BigQuery's data-staleness limit is 15 minutes for cost control, and this trade-off is documented against the five-minute committed-change requirement.
- Change events are applied idempotently, using a merge on the primary key and appropriate ordering/version handling, so retries do not create duplicate rows.
- CDC outage, regional promotion, and slot invalidation procedures include checkpointed replay or resynchronization, with documented validation of completeness and freshness before normal operation resumes.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny inter-namespace traffic by default, and Binary Authorization admits only images built by the approved pipeline.
- Columns containing personal data are covered by BigQuery policy tags, and datasets use customer-managed encryption keys.

## 9. Observability

- Service-level indicators are request success rate and latency measured at the load balancer. Alerts cover one-hour and six-hour error-budget burn rates.
- Dashboards and alerts cover database and cross-region replica lag, analytics-replica lag, CDC freshness and backlog, replication-slot/WAL retention and primary-storage pressure, node capacity by zone, autoscaler state, load-balancer health, and failover status.
- Recovery objectives and dependency error budgets are reviewed using measured telemetry.

## 10. Testing and operations

- A zone-failure game day is conducted quarterly.
- A full regional recovery rehearsal is conducted at least annually and includes detection and declaration, load-balancer failover, database replica promotion, application/configuration/credential cutover, recovery-backend readiness validation, CDC slot/replay or resynchronization behavior, and restoration validation.
- Each exercise records timings for every recovery step, measured replica lag, measured RTO/RPO, identified corrective actions, and tracked completion before relying on the design for production.