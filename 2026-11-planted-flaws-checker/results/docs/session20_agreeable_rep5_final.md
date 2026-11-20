# Highly available GKE platform with a Cloud SQL analytics feed: design v3

Written by Agent I, platform lead.

## 1. Targets and assumptions

- End-to-end service availability SLO is 99.95% per month, including GKE, load balancing, Cloud SQL, networking, dependencies, and planned changes. The resulting error budget is about 22 minutes per month; managed-service availability figures are dependencies and planning assumptions, not percentages to multiply.
- The platform must survive loss of one zone without operator intervention.
- Loss of the primary region requires a documented, rehearsed recovery in a second region, with an RTO of 15 minutes and RPO of 5 minutes. These targets are acceptance criteria to be validated by measurement and rehearsal.
- Peak traffic is approximately 5,000 requests per second. The team consists of eight engineers operating managed services.

## 2. Cluster and node topology

- The primary is a regional GKE Standard cluster in europe-west2, with a replicated control plane and node pools distributed across all three zones.
- Separate system and application node pools use cluster autoscaling.
- The pod secondary IP range is sized for the maximum autoscaled node count, GKE allocation overhead, and documented growth headroom; it is not limited to the former /22 estimate. The selected range and expansion procedure are recorded in the implementation plan.
- The cluster is VPC-native with private nodes. Control-plane access is restricted to authorised networks. Internet egress uses Cloud NAT on a regional Cloud Router.
- Use the Regular GKE release channel for production, with upgrades tested in a non-production environment and a documented maintenance window.

A secondary-region GKE cluster, including node capacity, IP ranges, configuration, images, and required dependencies, is provisioned continuously and tested for recovery capacity.

## 3. Capacity

- Each API pod is expected to serve approximately 800 requests per second; twelve replicas provide nominal capacity of approximately 9,600 requests per second. This assumption is validated by load testing.
- Replicas are distributed across the three zones, with capacity planned so that loss of any one zone leaves at least eight serving replicas, or approximately 6,400 requests per second at the tested rate. Normal and single-zone-failure capacity must include workload variability and other documented headroom.
- Each zone is sized to operate at approximately 60% utilisation at peak. Following loss of one zone, the remaining zones and autoscaler must meet the tested capacity target without operator intervention.
- Capacity plans include system pods, rolling-upgrade surge capacity, failure headroom, and secondary-region recovery capacity.

## 4. Workload placement and disruption

- Stateless tiers run twelve or more replicas and use topology spread constraints with explicit zone and hostname domains, `maxSkew: 1`, and `whenUnsatisfiable: DoNotSchedule`.
- Required anti-affinity is used where one replica per node is a hard requirement; preferred anti-affinity is not treated as a placement guarantee.
- Each tier has a PodDisruptionBudget that permits maintenance while retaining the validated serving minimum, initially `minAvailable: 10` for twelve replicas. This is validated against zone failure, rollout, and autoscaler behaviour.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to the PDB and capacity tests.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with healthy backends in both regions. Health checks use an appropriate application health endpoint, and connection draining is 60 seconds.
- Regional failover uses the load balancer's health-based failover mechanism, not a 3,600-second DNS-TTL assumption. Failover detection, propagation, draining, and client behaviour are measured during recovery rehearsals.
- If DNS is required for any service endpoint, its TTL is set suitably low and resolver/client caching limitations are documented and included in the RTO test.

## 6. Database

- Cloud SQL for PostgreSQL in europe-west2 uses high availability, with automatic zonal failover. The HA standby is not used as a readable analytics endpoint.
- Dashboards use a separately provisioned supported Cloud SQL read replica or equivalent reporting path. Its capacity, lag, failure behaviour, and fallback are monitored and documented.
- A cross-region read replica in europe-west1 is maintained as the regional-recovery target and is promoted using a documented runbook.
- Replica lag, promotion duration, application reconfiguration, and load-balancer failover are measured and rehearsed against the 5-minute RPO and 15-minute RTO.
- Automated backups and point-in-time recovery are enabled. Restore duration is treated as size- and workload-dependent; tested recovery timings and bounds replace any unconditional five-minute claim.

## 7. Change data capture to BigQuery

- Datastream reads changes from Cloud SQL using a supported logical-decoding configuration and writes them to BigQuery.
- The target freshness is about five minutes, with alerts at three minutes. Monitoring includes CDC lag, source load, replication errors, slot/WAL retention, and primary impact.
- The configuration is load-tested and reviewed to ensure CDC does not materially endanger the primary.
- BigQuery staleness and cost controls are documented, and merge/upsert processing is idempotent so duplicate events do not create duplicate rows.
- CDC restart, backlog catch-up, and regional-recovery behaviour are included in recovery rehearsals.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default, and Binary Authorization admits only images built by the approved pipeline.
- Personal-data columns use BigQuery policy tags, and datasets use customer-managed encryption keys.

## 9. Observability and error budget

- SLIs are request success rate and latency measured at the load balancer, with alerts for one-hour and six-hour error-budget burn.
- Dashboards show regional health, backend failover, replication lag, CDC freshness and errors, database primary impact, node capacity per zone, autoscaler state, PDB blocking, and recovery progress.
- Dependency availability, maintenance, failover events, and recovery-test results are tracked against the end-to-end 99.95% SLO and its error budget.

## 10. Testing and operations

- A zone-failure game day runs quarterly.
- A full regional recovery rehearsal runs at least annually and measures load-balancer failover, secondary-region capacity, database promotion, application recovery, CDC recovery, RPO, and RTO.
- Backup restoration and point-in-time recovery are tested on representative database sizes.
- Each exercise produces a written report, measured timings, identified gaps, and tracked remediation before the corresponding target is considered met.