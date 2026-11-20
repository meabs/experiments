# Highly available GKE platform with a Cloud SQL analytics feed: design v2

## 1. Targets

- Service availability target: 99.95% per month, with an approximately 22-minute monthly error budget.
- The design must tolerate loss of one zone without operator intervention.
- Loss of a whole region must have a documented and rehearsed recovery in a second region, with a 15-minute RTO and 5-minute RPO. These objectives are acceptance criteria to be demonstrated in recovery exercises.
- Peak traffic is approximately 5,000 requests per second. The team consists of eight engineers using managed services.
- Availability is an end-to-end objective; component availability figures are not multiplied or otherwise treated as proving the platform target. The error budget includes application, dependencies, maintenance, and recovery behavior.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled.
- The pod secondary IP range is sized from the maximum autoscaled node and pod count, with headroom, rather than being fixed at /22. Initial planning uses at least a /20 and must be confirmed against the final maximum node count and GKE IP-allocation model.
- The cluster is VPC-native with private nodes. Access to the control-plane endpoint is limited to authorised networks. Egress to the internet goes through Cloud NAT on a regional Cloud Router.
- Use the GKE Stable release channel for production, subject to confirming application compatibility and support requirements. A tested maintenance window runs on Sunday from 02:00 to 06:00 local time.

## 3. Capacity

- Each API pod has a measured capacity of approximately 800 requests per second under representative load. At least eight replicas are deployed initially, providing tested headroom above the 5,000-request-per-second peak; the final replica and node counts are set by load testing and include failure headroom.
- Each zone's node pool is sized and autoscaled so that peak traffic remains within the tested operating range after loss of one zone. The design must be validated by load testing and a zone-failure game day; 90% utilisation is not assumed to provide adequate margin.
- Autoscaler scale-up time, quotas, IP capacity, and startup time are included in the capacity test.

## 4. Workload placement and disruption

- Stateless tiers run at least eight replicas, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Required hostname anti-affinity is used where the replica count and capacity make one replica per node an explicit requirement; otherwise topology spread and tested node capacity are the placement guarantees.
- Each tier has a PodDisruptionBudget that preserves the tested serving capacity while allowing voluntary evictions and upgrades (initially `minAvailable: 7` for eight replicas, subject to load-test results). The PDB must not be set to the full replica count.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, and upgrade behavior is tested with the PDB and topology constraints.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use the application's `/healthz` endpoint, and connection draining is 60 seconds.
- Regional failover uses the load balancer's health-based backend failover and is exercised during recovery rehearsals. DNS is not the primary failover mechanism.
- If DNS is used for any auxiliary endpoint, its TTL is suitably low and resolver caching limitations are documented; a 3,600-second TTL is not used for the customer-facing regional failover.
- The regional recovery runbook covers application deployment and capacity, load-balancer routing, database promotion, secrets/configuration, validation, and rollback.

## 6. Database

- The transactional database is Cloud SQL for PostgreSQL in europe-west2 with high availability enabled: a primary in one zone and a standby in another, with automatic regional failover.
- The HA standby is not used as a read endpoint. Dashboards use a separately provisioned and appropriately sized Cloud SQL read replica (or another explicitly supported analytics-read architecture), with its expected consistency, lag, and failure behavior documented.
- Automated backups and point-in-time recovery are enabled.
- A cross-region read replica in europe-west1 is the target for regional recovery and is promoted by a documented, access-controlled runbook.
- Cross-region replication lag is monitored. The measured lag and promotion process must demonstrate the 5-minute RPO and 15-minute RTO during rehearsals; the RPO is conditional on the observed replication lag at the time of failure.
- Backup restore time is database-size-dependent and is not assumed to be five minutes. A measured restore objective, restore procedure, and restore validation are maintained and tested.

## 7. Change data capture to BigQuery

- Datastream reads changes from Cloud SQL PostgreSQL using the supported logical-decoding configuration and writes them to BigQuery. The target freshness is five minutes, and an alert fires at three minutes.
- Replication slots, WAL retention, slot growth, Datastream health, and source impact are monitored. Retention limits and an operational procedure prevent CDC lag from endangering primary-database storage or performance.
- The BigQuery destination's staleness limit is 15 minutes to control query costs, while the operational freshness objective remains five minutes.
- Change events are applied idempotently, using a merge on the primary key so duplicate delivery does not create duplicate rows.
- CDC behavior during database failover, regional recovery, replica promotion, and Datastream restart is documented and tested.

## 8. Security

- Workloads reach Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default, and Binary Authorization admits only images built by the approved pipeline.
- Columns holding personal data are covered by policy tags in BigQuery, and datasets use customer-managed encryption keys.

## 9. Observability

- Service-level indicators are request success rate and latency measured at the load balancer. Alerts cover error-budget burn over one-hour and six-hour windows.
- Dashboards show replication lag for the cross-region and analytics replicas, CDC freshness, logical-slot/WAL retention, node-pool capacity per zone, autoscaler state, load-balancer health, and regional failover status.
- Alerts and runbooks cover loss of a zone, database failover, replica lag, CDC degradation, exhausted IP capacity, and failed node upgrades.

## 10. Testing and acceptance

- A zone-failure game day is conducted every quarter.
- A full regional recovery rehearsal is conducted at least annually, with a written report.
- Load, autoscaling, node-upgrade, database-promotion, backup-restore, CDC-failure, and regional-failover tests verify the stated capacity, availability, RTO, RPO, and five-minute CDC-freshness objectives before production launch and after material changes.