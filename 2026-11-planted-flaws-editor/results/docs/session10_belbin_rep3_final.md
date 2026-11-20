# Highly available GKE platform with a Cloud SQL analytics feed: design v2

## 1. Targets and SLO

- Customer-facing stateless web/API service for one continent; peak traffic is 5,000 requests/second.
- End-to-end monthly availability target is 99.95% (about 22 minutes of error budget). This is measured at the load balancer and includes the application, database, and required dependencies; nominal component percentages are not treated as additive.
- The platform must survive loss of one zone without operator action.
- Regional loss has a documented and rehearsed recovery in a second region, with a 15-minute RTO and a 5-minute RPO demonstrated by measured tests.
- The team is eight engineers using managed services.

## 2. GKE topology and capacity

- One regional GKE Standard cluster in `europe-west2`, with a regional control plane and node pools across all three zones.
- Separate system and application node pools, each with cluster autoscaling, quota headroom, and tested maximum sizes.
- Use a pod secondary range sized for the maximum autoscaled population, surge upgrades, and failure recovery; `/22` is insufficient. Record the chosen range and expansion plan after calculating GKE per-node allocation.
- Private VPC-native nodes access Google APIs through Private Google Access or Cloud NAT. The control-plane endpoint is restricted to authorised networks.
- Use the Regular release channel (or Stable if compatibility testing selects it), with a documented upgrade and rollback policy and a weekly maintenance window.

## 3. Application capacity and placement

- Baseline at least seven API replicas; capacity tests must demonstrate at least 5,000 requests/second with headroom and after loss of one zone. Use resource-based HPA with defined minimum, maximum, requests, limits, and scale-up behavior.
- Size each zonal node pool and autoscaler limits for peak load after a zone loss, rolling upgrades, and pod rescheduling; validate quotas and IP capacity.
- Spread replicas across zones with topology spread constraints (`maxSkew: 1`, `DoNotSchedule`) and required hostname anti-affinity where one-per-node placement is required.
- Use a PodDisruptionBudget that permits controlled maintenance (initially `minAvailable: 6` for seven replicas, subject to upgrade testing), rather than blocking all voluntary eviction. Surge upgrades use `maxSurge: 1`, `maxUnavailable: 0`; test drains and rollback.

## 4. Traffic and regional recovery

- Use a global external Application Load Balancer with healthy backends in both regions and an explicit health-based failover policy. Do not rely on a 3,600-second DNS TTL for the 15-minute RTO; any DNS used for bootstrap or control has a bounded TTL and documented caching limitations.
- Health checks must represent application readiness, including required database connectivity, and connection draining is 60 seconds.
- The regional recovery runbook sequences: declare failure; fence the old primary and prevent writes/split-brain; promote the cross-region Cloud SQL replica; validate replication position and data-loss bound; update application connection configuration/secrets; enable the secondary-region backend; shift traffic; and validate writes and monitoring. The procedure is rehearsed annually and must complete within the measured RTO.

## 5. Cloud SQL

- Cloud SQL for PostgreSQL has regional HA enabled for automatic zonal failover.
- The HA standby is not a reporting endpoint. Provision a separate read replica for dashboards, size it for reporting load, and monitor lag, health, and failover behavior.
- Maintain a cross-region read replica in `europe-west1`. Monitor lag continuously and alert/escalate when the measured lag threatens the 5-minute RPO. Promotion, fencing, connection cutover, and post-promotion validation are documented and tested.
- Automated backups and point-in-time recovery are enabled. Backup restore time is not assumed to be five minutes or independent of database size; establish measured restore RTO/RPO at production scale and include it in recovery rehearsals.
- Define migration, backup, failover, and replica-promotion change controls, including rollback and application write-fencing.

## 6. CDC to BigQuery

- Datastream reads Cloud SQL PostgreSQL changes using a supported logical-decoding configuration. Provision and monitor replication slots, WAL retention, source CPU/IO, stream lag, and slot growth; alert before CDC can endanger the primary.
- Target freshness is five minutes, with alerting at three minutes. Duplicate-safe application uses documented keys and merge semantics.
- Document Datastream behavior during Cloud SQL failover and regional promotion, including stream restart, slot handling, and reconciliation. Validate that no committed changes are silently lost and that recovery meets the five-minute RPO.
- BigQuery freshness monitoring is based on event/ingestion timestamps and reconciliation, not an assumed destination staleness setting. Personal-data policy tags and customer-managed encryption keys remain enabled.

## 7. Security and observability

- Use Workload Identity Federation for GKE with one Google service account per tier and no exported keys.
- Default-deny network policies separate namespaces. Binary Authorization admits only pipeline-built images.
- SLIs are load-balancer request success rate and latency; alert on one-hour and six-hour error-budget burn. Dashboards include zonal capacity, autoscaler state, database/replica lag, backup status, CDC freshness, WAL/slot growth, and failover readiness.

## 8. Validation and operations

- Before production, run load tests at peak and post-zone-loss capacity, node-drain/upgrade tests, database failover tests, CDC interruption/restart tests, and restore measurements.
- Conduct a zone-failure game day quarterly and a full regional recovery rehearsal at least annually, with written results, measured RTO/RPO, corrective actions, and a build/runbook ownership checklist.