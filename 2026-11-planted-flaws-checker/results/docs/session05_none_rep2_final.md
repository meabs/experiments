# Highly available GKE platform with a Cloud SQL analytics feed: design v3

Written by Agent I, the platform lead.

## 1. Targets

- Customer-facing web application for users in one continent.
- Service availability SLO: 99.95% per month, measured at the global load balancer for healthy, correctly routed requests. The error budget is approximately 22 minutes per month.
- The design uses independent failure domains and tested managed-service configurations; individual component availability figures are not multiplied to claim the end-to-end SLO. Dependency outages, maintenance, and exclusions are documented in the SLO.
- Survive loss of one zone without operator intervention.
- Survive loss of the whole region through a documented and rehearsed recovery in a second region, with target RTO of 15 minutes and RPO of 5 minutes. These targets are commitments only after promotion, replication lag, application reconfiguration, and validation have been measured in rehearsals.
- Peak traffic is approximately 5,000 requests per second. The design is for eight engineers on a managed-service budget.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled.
- The pod secondary IP range is sized from the configured max-pods-per-node, maximum node count, upgrade surge, and additional growth headroom. It is substantially larger than /22 (initial allocation: /18, subject to final capacity calculation).
- The cluster is VPC-native with private nodes. Access to the control-plane endpoint is limited to authorised networks. Internet egress uses Cloud NAT on a regional Cloud Router.
- The cluster uses the Regular release channel, unless a documented feature requirement requires another supported channel. Versions and upgrades are validated before production rollout.
- A weekly maintenance window runs on Sunday from 02:00 to 06:00 local time.

## 3. Capacity

- The API tier starts with at least seven replicas. Each API pod serves approximately 800 requests per second under representative load testing; seven replicas therefore provide 5,600 requests per second before additional safety margin. Resource requests and limits, replica count, and required headroom are validated by load testing.
- Each zone's node pool is sized for appropriate headroom at peak traffic. After loss of one zone, the remaining zones and autoscaler must carry the peak traffic while new capacity is scheduled; this behavior and autoscaler reaction time are tested.
- Maximum node counts, pod IP capacity, quota, regional capacity, and upgrade surge capacity are tested before production.

## 4. Workload placement and disruption

- Stateless tiers run at least seven replicas, spread across zones using topology spread constraints with maxSkew 1 and `whenUnsatisfiable: DoNotSchedule`.
- Required hostname anti-affinity is used when one replica per node is a hard requirement; otherwise any preferred anti-affinity use is documented as a best-effort placement policy rather than a guarantee.
- Each tier has a PodDisruptionBudget that permits controlled voluntary disruption while preserving service capacity (initially `minAvailable: 6` for seven replicas). The value is validated against capacity, upgrade, and zone-failure testing.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to sufficient quota and reserved pod/node capacity.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use the application's `/healthz` endpoint, and connection draining is 60 seconds.
- Regional routing and failover use the load balancer's health-based traffic management. A DNS-only failover with a 3,600-second TTL is not used for the 15-minute RTO.
- The regional recovery runbook covers declaring the incident, fencing or disabling the failed region, routing traffic to the second region, promoting the database replica, changing application database endpoints and configuration, validating the application and load-balancer health, checking CDC, and restoring normal routing. Failover timing is verified in rehearsals.

## 6. Database

- The transactional database is Cloud SQL for PostgreSQL in europe-west2 with high availability enabled: a primary in one zone and a standby in another, with automatic intra-region failover. Automated backups and point-in-time recovery are enabled.
- The HA standby is not used as a reporting endpoint. Analytics dashboards use a separately provisioned, supported read replica (or an explicitly approved BigQuery path), sized and monitored so reporting cannot overload the primary.
- A cross-region read replica in europe-west1 is the regional-recovery target. Its replication lag is monitored, and the recovery runbook specifies promotion, write fencing, application connection changes, and post-promotion validation.
- The five-minute RPO is validated by measuring replica lag under normal and peak load and during failure scenarios. Backup restore and replica-promotion times are measured during rehearsals; restore time is not assumed to be five minutes or independent of database size.
- If a bad migration corrupts data, recovery uses point-in-time or backup restore according to the runbook, with tested, size-dependent recovery objectives.

## 7. Change data capture to BigQuery

- Datastream reads committed changes from the Cloud SQL primary through a validated logical-decoding configuration and writes them to BigQuery without an unsafe load on the primary.
- The target is for every committed change to reach BigQuery within five minutes. Datastream lag, source impact, destination failures, quotas, and backpressure are monitored; alerts fire before the objective is missed (initially at three minutes).
- CDC behavior during regional failover, replica promotion, reconnect, replay, and duplicate delivery is tested and documented. The pipeline provides the required idempotency and preserves inserts, updates, and deletes; a primary-key merge alone is not assumed to preserve change history or correctly handle all operations.
- The BigQuery destination staleness limit is set according to the five-minute freshness requirement and validated against cost and query requirements; a 15-minute limit is not used if it permits violating the committed-change objective.

## 8. Security

- Workloads reach Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default, and Binary Authorization admits only images built by the approved pipeline.
- Columns containing personal data are covered by BigQuery policy tags, and datasets use customer-managed encryption keys.

## 9. Observability

- Service level indicators are request success rate and latency measured at the load balancer. Alerts cover one-hour and six-hour error-budget burn rates.
- Dashboards show regional routing and health, database HA and cross-region replica lag, read-replica health, CDC freshness and backpressure, node-pool capacity by zone, quotas, and autoscaler state.
- Alerts and runbooks cover replication lag, promotion readiness, CDC replay, and failure of analytics isolation.

## 10. Testing and operations

- A zone-failure game day is conducted every quarter.
- A full regional recovery rehearsal is conducted at least annually and after material architecture changes.
- Each exercise records measured RTO, RPO, replica lag, restore/promotion time, routing convergence, CDC freshness, application validation, load-balancer health, and corrective actions.
- The team maintains the capacity calculations, maintenance procedures, failover runbook, SLO definitions, and tested assumptions as build prerequisites.