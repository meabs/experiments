# Highly available GKE platform with a Cloud SQL analytics feed: design v4

Written by Agent I, the platform lead.

## 1. Targets

- The platform SLO is 99.95% monthly availability for successful, correctly routed customer requests, measured at the global load balancer. The resulting monthly error budget is approximately 22 minutes.
- Availability is not calculated by multiplying independent component availability figures. Dependencies, maintenance, and failover paths are accounted for in the end-to-end SLO and error-budget policy, validated through monitoring and game days.
- Survive the loss of one zone without operator intervention.
- Survive loss of the whole region through a documented, rehearsed recovery in a second region, with an RTO of 15 minutes and an RPO of 5 minutes.
- Peak traffic is about 5,000 requests per second. The team is eight engineers on a managed-service budget.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled.
- The pod secondary IP range is calculated from the maximum planned nodes, per-node alias-IP allocation, upgrade surge nodes, and growth capacity, with a documented expansion plan. The initial allocation is /18, subject to VPC IP planning and validation against the actual GKE allocation model.
- The cluster is VPC-native with private nodes. Access to the control-plane endpoint is limited to authorised networks. Egress to the internet goes through Cloud NAT on a regional Cloud Router.
- The cluster uses the Regular release channel for production. Required versions and features are validated before adoption. A weekly maintenance window runs on Sunday from 02:00 to 06:00 local time.

## 3. Capacity and acceptance gates

- Each API pod can serve about 800 requests per second, subject to load-test validation. At least seven API replicas are deployed; nominal capacity is therefore at least 5,600 requests per second before failure or maintenance headroom.
- Each zone's node pool is sized so that, after loss of one zone, the two remaining zones can sustain at least 6,000 requests per second at the defined latency SLO, with explicit CPU, memory, autoscaler, quota, and scheduling headroom. The design does not rely on approximately 90% utilisation or merely meeting the 5,000-RPS peak.
- Before build approval, sustained load tests must demonstrate at least 6,000 RPS at the defined latency SLO in steady state and during one-zone loss. Tests must verify autoscaling, quotas, pod-range capacity, topology spread, required anti-affinity, and PDB behavior, including node drains while seven or more replicas remain available.
- Capacity assumptions, autoscaler limits, pod-range exhaustion, and two-zone operation are tested before production and during zone-failure exercises.

## 4. Workload placement and disruption

- Stateless tiers run at least seven replicas, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Required pod anti-affinity on the hostname key prevents two replicas of a tier from sharing a node, provided sufficient nodes are available; scheduling alerts identify insufficient capacity.
- Each tier has a PodDisruptionBudget with `minAvailable: 5`. Surge capacity, spread constraints, and the validated degraded-state capacity plan preserve the availability target during voluntary disruption.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`.

## 5. Traffic

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use the application's `/healthz` endpoint, and connection draining is set to 60 seconds.
- Regional failover uses the load balancer's health-based backend failover. DNS is not used as the primary failover mechanism.
- Global load-balancer convergence, connection draining, application readiness, and client behavior are tested end to end during regional recovery.

## 6. Database

- The transactional database is Cloud SQL for PostgreSQL in europe-west2 with high availability enabled: a primary in one zone and a standby in another, with automatic failover inside the region. Automated backups and point-in-time recovery are enabled.
- The HA standby is not used for reporting. Dashboards use a separately provisioned, supported Cloud SQL read replica or BigQuery, with its read-only behavior, lag monitoring, and failover behavior documented.
- A cross-region read replica in europe-west1 is the target of regional recovery and is promoted by a documented runbook. Replica lag is monitored continuously; promotion is permitted only when measured lag supports the 5-minute RPO, or the incident records the resulting data-loss risk.
- Backup restoration objectives are measured for the actual database size and workload. Restore and point-in-time recovery are tested regularly; no size-independent five-minute guarantee is assumed.
- The regional recovery runbook covers database promotion, validation of the promoted endpoint, application configuration and secrets, CDC reconfiguration, and traffic failover. A pre-created second-region GKE target is maintained at sufficient baseline capacity and is scaled during recovery.

## 7. Change data capture to BigQuery

- Datastream reads changes from the Cloud SQL primary through PostgreSQL logical decoding and writes them to BigQuery. The target freshness is five minutes, and a replication-lag alert fires at three minutes.
- The logical replication slot, WAL retention, storage growth, and Datastream failure modes are monitored. Runbooks pause or reconfigure CDC safely when necessary so lag or slot growth cannot endanger primary-database capacity.
- The BigQuery destination's data-staleness limit is 15 minutes to control query costs. Change events are applied with a merge on the primary key, so duplicate events do not create duplicate rows.
- CDC regional failover and restart procedures, including slot/WAL safeguards, are included in the recovery rehearsal.

## 8. Security

- Workloads reach Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default, and Binary Authorization admits only images built by the pipeline.
- Columns holding personal data are covered by policy tags in BigQuery, and datasets use customer-managed encryption keys.
- Recovery-region secrets, identities, keys, and permissions are provisioned and tested before an incident.

## 9. Observability

- Service-level indicators are request success rate and latency measured at the load balancer. Alerts cover one-hour and six-hour error-budget burn rates.
- Dashboards show replication lag, CDC freshness, node-pool capacity per zone, pod-range utilisation, autoscaler state, load-balancer backend health, and failover status.
- Alerts and runbooks cover Cloud SQL storage/WAL growth, read-replica lag, cross-region replica lag, and recovery readiness.

## 10. Testing and build gates

- A zone-failure game day is held every quarter.
- A full regional recovery rehearsal is held every year, including pre-provisioned GKE capacity, load-balancer health-based failover and convergence, application readiness, Cloud SQL promotion, promoted-endpoint consumption, secrets and configuration, CDC restart and validation, and rollback.
- Backup restores, point-in-time recovery, replica promotion, and measured restore times are tested regularly.
- Build approval requires steady-state and one-zone-loss load tests to sustain **at least 6,000 RPS** at the defined latency SLO, and requires verified PDB, topology, node, quota, autoscaler, and pod-range behavior.
- Regional recovery acceptance requires measured RTO no greater than 15 minutes and measured RPO no greater than 5 minutes, including load-balancer convergence, database promotion, application readiness, secrets/configuration validation, safe draining of in-flight traffic, and CDC restart. Service is not reopened until database, secrets, readiness, and CDC checks pass.
- Each exercise produces a written report, remediation actions, and updated measured RTO/RPO evidence.