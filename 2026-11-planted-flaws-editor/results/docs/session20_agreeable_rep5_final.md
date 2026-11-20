# Highly available GKE platform with a Cloud SQL analytics feed: design v2

Written by Agent I, the platform lead.

## 1. Targets and availability model

- Customer-facing availability SLO is 99.95% per month, measured by successful, correctly served requests at the global load balancer. The 99.95% target is an end-to-end SLO, not the product of separate component availability claims.
- The platform must survive loss of one zone without operator action.
- Regional loss has a documented and rehearsed recovery in a second region, with an RTO of 15 minutes and an RPO of 5 minutes. The measured cross-region database lag must remain within the RPO.
- Peak traffic is about 5,000 requests per second. The team is eight engineers using managed services.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with a replicated regional control plane and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling and a documented maximum sized for zone loss, upgrade surge, and peak load.
- The VPC-native cluster uses a pod secondary range sized from the maximum node count, 110 pods per node, and upgrade/headroom requirements; `/18` is the initial allocation and will be validated against the actual maximum.
- Nodes are private. Control-plane access is limited to authorised networks. Internet egress uses Cloud NAT.
- Use the Regular release channel. Upgrades follow a tested policy with a Sunday 02:00–06:00 local-time maintenance window.

## 3. Capacity

- Each API pod serves about 800 requests per second; six replicas provide capacity above the 5,000 requests-per-second peak.
- Capacity and autoscaler limits are tested for normal operation, loss of one zone, and rolling upgrades. After zone loss, the remaining zones must meet the documented serving-capacity target without operator action.

## 4. Workload placement and disruption

- Stateless tiers run six replicas with topology spread constraints across zones (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Required hostname anti-affinity is used where node-level separation is required; capacity limits and pending-pod alerts cover cases where placement cannot be met.
- Each tier has a disruption budget of `minAvailable: 5`, preserving service capacity while allowing voluntary maintenance. Surge upgrades use `maxSurge: 1` and `maxUnavailable: 0`; upgrade drills verify that capacity and disruption budgets do not block progress.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use `/healthz`, and connection draining is 60 seconds.
- Regional failover uses the load balancer's health-based backend failover. DNS is not the failover control plane; any DNS records have a TTL and client-cache limitations documented and tested against the RTO.
- Regional traffic is enabled only after the recovery gate completes in order: promote and validate the Cloud SQL replica, re-point Datastream and verify fresh CDC, start and pass readiness checks for the recovery application, then enable the recovery region in global load-balancer routing.
- The regional recovery runbook covers provisioning or selecting the standby GKE capacity, database promotion, application configuration/secrets, CDC reconfiguration, traffic cutover, validation, and rollback. A full rehearsal occurs annually.

## 6. Database

- Cloud SQL for PostgreSQL in europe-west2 uses high availability with automatic same-region failover. Its HA standby is not used as a read endpoint.
- Dashboards use a separately provisioned supported read replica, with documented sizing, lag monitoring, and failure behavior.
- A cross-region read replica in europe-west1 is the regional-recovery target. Its observed asynchronous lag is monitored and must support the five-minute RPO; promotion is tested in every recovery rehearsal.
- Automated backups and point-in-time recovery are enabled. Restore RTO is size- and workload-dependent and is established by measured restore drills rather than an unconditional five-minute claim. The measured target and latest drill results are recorded.

## 7. Change data capture to BigQuery

- Datastream reads Cloud SQL changes using a supported logical-decoding configuration and writes them to BigQuery. Configuration, replication slots, retention, and primary-resource impact are reviewed before production.
- The committed-change freshness objective is five minutes, measured from commit to queryable BigQuery data. Alerts fire at three minutes; the recovery plan covers lag, slot pressure, and Datastream failure.
- BigQuery data staleness is limited to 15 minutes for cost control, with the five-minute freshness objective monitored separately.
- Change application is idempotent (merge on the primary key); replay and duplicate-event behavior are tested. CDC is re-pointed and validated after regional database promotion.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only pipeline-built images.
- Personal-data columns use BigQuery policy tags, and datasets use customer-managed encryption keys.

## 9. Observability and error budget

- SLIs are load-balancer request success rate and latency. Alerts cover one-hour and six-hour error-budget burn rates.
- Dashboards show regional and zonal capacity, autoscaler state, pod placement, database/read-replica/cross-region lag, backup/restore results, Datastream freshness and slot health, and BigQuery staleness.
- The end-to-end error budget includes load balancing, GKE, Cloud SQL, dependencies, and planned maintenance; component availability assumptions are not summed or multiplied to claim the platform SLO.

## 10. Testing and acceptance

- Quarterly zone-failure game days verify automatic rescheduling, autoscaling, traffic handling, and database behavior.
- Annual regional recovery rehearsals measure RTO, RPO, database promotion, application cutover, and CDC recovery.
- Upgrade, restore, read-replica failure, Datastream lag/failure, and capacity tests are completed before production launch, with written reports and remediation tracking.