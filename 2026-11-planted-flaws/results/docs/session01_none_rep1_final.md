# Highly available GKE platform with a Cloud SQL analytics feed: design v3

Written by Agent I.

## 1. Targets and availability model

- Customer-facing stateless web/API service target is 99.95% monthly availability, measured at the global load balancer for successful requests and latency. This allows approximately 22 minutes of monthly unavailability. Planned maintenance is included in this SLO; maintenance is scheduled within the documented window and exclusions, but is not silently excluded from availability measurement.
- The design survives loss of one zone without operator intervention.
- Loss of the primary region is recovered through a rehearsed runbook in a second region, with an RTO of 15 minutes and an RPO target of 5 minutes.
- Peak traffic is approximately 5,000 requests per second. The team is eight engineers operating managed services.
- The 99.95% target is an end-to-end service SLO, not the result of multiplying or averaging independent component availability claims. Error budgets and dependency objectives will be allocated to GKE, load balancing, Cloud SQL, networking, and supporting systems, with capacity and failover tested against the end-to-end objective.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with a replicated regional control plane and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled.
- The cluster is VPC-native with private nodes. The Pod secondary range is sized from the configured max-pods-per-node, maximum node count, surge capacity, and regional-failure headroom. A preliminary /19 allocation is reserved for the expected approximately 30-node maximum, subject to validation against the selected GKE IP-allocation mode; expansion capacity is planned.
- Control-plane access is limited to authorized networks.
- Internet egress uses Cloud NAT through a regional Cloud Router.
- Use the GKE Regular release channel, with release qualification and a weekly Sunday 02:00–06:00 local maintenance window plus appropriate maintenance exclusions.

## 3. Capacity

- Each API pod serves approximately 800 requests per second under representative load. Six replicas provide capacity above the 5,000-request-per-second peak, with resource requests and limits validated by load testing.
- Each zone is sized for approximately 60% utilization at peak. Following loss of one zone, the remaining zones must have sufficient preplanned and autoscalable capacity to serve traffic while maintaining required control-plane and system-pod headroom.
- Autoscaler maximums, quotas, node-pool surge capacity, and Pod IP capacity are tested during zone-failure exercises.

## 4. Workload placement and disruption

- Stateless tiers run six replicas with topology spread constraints across zones (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Preferred hostname anti-affinity is used, with capacity validation ensuring replicas do not unnecessarily co-locate.
- Each tier has a disruption budget that permits controlled voluntary disruption while preserving service capacity, initially `minAvailable: 5` for six replicas. The value is validated against drain, upgrade, and zone-failure behavior.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to the disruption budgets and available capacity.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with application backends in both regions.
- Health checks use a dedicated health endpoint that reflects readiness to serve traffic. Connection draining is 60 seconds.
- Regional failover uses the load balancer's health-based backend failover and is tested with loss of the primary region. DNS is not the primary failover mechanism; any DNS fallback uses a suitably low TTL and has resolver-caching limitations documented and tested.
- The secondary GKE region is provisioned ahead of time with application configuration, images, secrets, quotas, and tested capacity rather than being created during an incident.
- The recovery runbook covers declaring the regional incident, verifying replica lag, recording the last committed transaction recovered after promotion, promoting Cloud SQL, updating application database configuration and connection pools, validating the secondary region, shifting load-balancer traffic, and confirming service and CDC health. The procedure is rehearsed at least annually and must demonstrate the 15-minute RTO.
- The five-minute RPO is measured from transaction commit timestamps: after promotion, the team identifies the newest committed transaction recovered and records the timestamp difference from the failure boundary. Replica lag is a leading indicator and decision gate, but is not by itself evidence that the RPO was met.

## 6. Database

- Cloud SQL for PostgreSQL is deployed in europe-west2 with HA enabled: a primary and an automatic-failover standby in separate zones.
- The HA standby is not used for reporting; it is not treated as a readable endpoint.
- Analytics dashboards use a separately provisioned supported Cloud SQL read replica or analytics replica, with capacity, lag, availability, and promotion behavior monitored. Dashboard workloads are load-tested to verify they do not endanger transactional performance.
- A cross-region read replica in europe-west1 is maintained for regional recovery. Its replication lag is monitored and is part of the RPO decision. The recovery runbook promotes it, reconfigures the application, and verifies the timestamp of the last committed transaction recovered after promotion is within the five-minute RPO target.
- Automated backups and point-in-time recovery are enabled. Restore duration is not assumed to be size-independent: restore and recovery targets are measured for the production database size and tested regularly. A bad-migration procedure defines the selected recovery point, validation, application quiescing, and rollback.
- Regional recovery and backup restores are tested with written reports; measured results, including transaction-timestamp-based RPO and promotion timing, rather than unconditional five-minute claims, determine whether targets remain achievable.

## 7. Change data capture to BigQuery

- Datastream reads PostgreSQL changes from the primary using supported logical-decoding configuration and writes them to BigQuery.
- The target is for every committed change to reach BigQuery within approximately five minutes under normal operation. Freshness is monitored and an alert fires at three minutes; the BigQuery staleness limit is 15 minutes.
- Logical-replication prerequisites, replication-slot ownership, WAL retention, storage growth, and Datastream lag are monitored. Alerts and runbooks prevent a stalled consumer or slot from endangering primary storage.
- Changes are applied idempotently, using keys and merge semantics so duplicate delivery does not create duplicate rows.
- The regional-recovery runbook verifies Datastream behavior after Cloud SQL promotion, including source endpoint and slot/restart-position handling, reconfiguration or recreation where required, backfill/reconciliation, and freshness validation. CDC continuity and the five-minute objective are explicitly measured during recovery rehearsals.

## 8. Security

- Workloads use Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default.
- Binary Authorization admits only images built and signed by the approved pipeline.
- Personal-data columns in BigQuery use policy tags, and datasets use customer-managed encryption keys.

## 9. Observability

- SLIs are request success rate and latency measured at the global load balancer.
- Alerts use one-hour and six-hour error-budget burn rates.
- Dashboards show load-balancer health by region, replica and node-pool capacity per zone, autoscaler state, Cloud SQL primary and read-replica lag, cross-region replica lag, Datastream freshness and slot/WAL growth, BigQuery staleness, and recovery-runbook checkpoints.
- Alerts identify when replica lag or CDC lag makes the five-minute RPO or freshness objective unattainable.

## 10. Testing and operational readiness

- A zone-failure game day runs quarterly and verifies autonomous rescheduling, capacity, traffic serving, database behavior, and CDC.
- A full regional recovery rehearsal runs at least annually and measures promotion, application reconfiguration, load-balancer failover, CDC recovery, RTO, and RPO. RPO evidence includes the timestamp of the last committed transaction recovered after promotion.
- Upgrade, backup restore, bad-migration recovery, read-replica failure, Datastream interruption, and replication-slot/WAL safeguards are tested with written reports.
- Build approval requires the measured IP capacity, resource capacity, restore time, replica lag, CDC recovery behavior, and end-to-end availability assumptions to be recorded and reviewed.