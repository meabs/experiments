# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets and assumptions

- The customer-facing service SLO is 99.95% monthly availability, measured by successful requests and latency at the global load balancer. This permits approximately 22 minutes of monthly unavailability; the error budget is shared across GKE, load balancing, Cloud SQL, networking, deployments, and regional recovery.
- The design does not claim that independently stated managed-service availability figures mathematically compose to 99.95%. Dependency failures, maintenance, capacity, failover, and recovery are included in the end-to-end availability budget and reviewed against SLO measurements.
- The platform must operate without operator intervention after loss of one zone.
- Loss of a whole region requires a documented and rehearsed recovery in a second region, with a tested RTO objective of 15 minutes and RPO objective of 5 minutes. These are acceptance objectives, not assumed guarantees.
- Peak traffic is approximately 5,000 requests per second. The team has eight engineers and will prefer managed services and simple operational procedures.

## 2. Cluster and node topology

- Use one regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools distributed across all three zones. Maintain a separately provisioned warm recovery cluster in europe-west1.
- For **each cluster**, test and document a maximum of 48 nodes across system and application pools. This envelope includes autoscaler capacity, one-zone-loss headroom, and upgrade surge capacity. Use `maxPodsPerNode: 110` and validate the expected approximately `/24` PodCIDR allocation per node against the selected GKE configuration.
- Allocate a separately sized pod secondary range for each region. Use `/18` as the initial candidate for each cluster (64 `/24` blocks), subject to validation of actual GKE allocation, all pools, the 48-node maximum, surge, growth, quotas, and subnet design. Do not assume `/18` is universally sufficient; block scaling when IP, quota, or regional capacity headroom is unavailable.
- Reserve node capacity, quotas, IP ranges, secrets, configuration, and application capacity independently in the warm recovery region. Validate that it can serve the tested recovery load.
- Use separate system and application node pools, each with cluster autoscaling. Size capacity per zone so surviving zones have sufficient reserved/quota-backed capacity after a zone failure, including system pods, application pods, rollout surge, and scale-up time.
- Use the Regular release channel (or Stable if required by compatibility testing), not Rapid. Pin and test supported versions and use a maintenance window that permits upgrades to complete; a four-hour weekly window alone is not an availability guarantee.
- Use private nodes, VPC-native networking, authorized networks for control-plane access, and Cloud NAT for internet egress.
- Validate IP exhaustion, quotas, reservations, and range-expansion implications before production.

## 3. Capacity

- The stated capacity of approximately 800 requests per second per API pod is a planning estimate, not a guarantee. Load-test realistic requests, including CPU, memory, downstream database, network, and latency limits.
- Provision at least six application replicas only after resource-based testing confirms peak traffic, one-zone loss, rollout surge, and autoscaler convergence meet the SLO. Define requests, limits, and suitable workload-based scaling metrics.
- Verify that remaining zones and the warm recovery cluster can serve the required load, including system workload capacity, node startup time, quotas, reservations, and temporary upgrade capacity.

## 4. Workload placement and disruption

- Stateless tiers run six or more replicas, distributed across zones using topology spread constraints with `maxSkew: 1` and `whenUnsatisfiable: DoNotSchedule`.
- If one-replica-per-node separation is required, use required hostname anti-affinity and provision enough nodes. Preferred anti-affinity is not a guarantee.
- Use a PDB preserving tested minimum serving capacity; for six replicas, `minAvailable: 5` is the initial policy, subject to load and zone-failure testing. Do not use `minAvailable: 6` while claiming voluntary drains and upgrades can proceed.
- Use surge node upgrades with `maxSurge: 1` and `maxUnavailable: 0`, and test drains, upgrades, rescheduling, autoscaling, PDB interactions, and service capacity under load.
- Do not treat a PDB as protection against involuntary zone or node failure.

## 5. Traffic and regional recovery

- Use a global external Application Load Balancer with a backend in each region and health checks testing application readiness and critical dependencies. Configure and verify health-based regional failover.
- Do not rely on a 3,600-second DNS TTL for a 15-minute RTO. The normal regional failover path is the global load balancer. Any DNS used for endpoint switching must have documented TTL, resolver-cache limitations, and tested RTO contribution.
- Connection draining is 60 seconds unless testing supports another value.
- The recovery runbook must detect and fence the failed region, fail traffic over, use warm GKE capacity, promote/select the database, change application configuration and secrets, switch endpoints, validate reads and writes, and restart or reconfigure Datastream after promotion.
- The 15-minute RTO is accepted only when the complete sequence—warm capacity, load-balancer failover, database promotion and fencing, endpoint switching, and application validation—has been load-tested and measured.

## 6. Database

- Use Cloud SQL for PostgreSQL with regional HA enabled. The HA standby is for failover and is not a readable analytics endpoint.
- Provision a separate supported read replica for reporting. Size it for dashboard queries and monitor lag, load, failure state, and behavior during primary failover. Define whether dashboards fall back to the primary or become unavailable.
- Maintain a cross-region asynchronous read replica in europe-west1. Monitor lag and WAL/retention conditions. Demonstrate during representative load and regional-recovery rehearsal that the accepted data-loss window meets the 5-minute RPO objective. Define write quiescing/fencing, promotion, endpoint changes, validation, and application behavior.
- Keep backups and PITR enabled. Measure restore, WAL replay, validation, and application-recovery time at representative database sizes; recovery objectives are size- and configuration-dependent and must be retested after material growth.

## 7. Change data capture to BigQuery

- Configure Datastream using supported Cloud SQL logical-decoding prerequisites and least-privilege access. The source is the active primary, including the promoted regional primary.
- Target freshness is five minutes, with alerting at three minutes. Demonstrate it under peak write load and during replica/promotion scenarios.
- Monitor replication slots, WAL generation and retention, disk growth, Datastream lag/errors, backpressure, and BigQuery freshness. Use bounded retention and remediation procedures so CDC cannot exhaust primary storage.
- Define interruption, slot recreation, duplicate, missed-event, ordering, and regional-promotion behavior; reconcile or backfill where required.
- Apply events idempotently and validate deletes, updates, ordering, and duplicates. Set BigQuery staleness limits consistent with the freshness objective and query-cost trade-off.

## 8. Security

- Use Workload Identity Federation for GKE, one least-privilege service account per tier, and no exported keys.
- Deny cross-namespace traffic by default with network policies.
- Use Binary Authorization for approved, attested images.
- Apply BigQuery policy tags to personal-data columns and use customer-managed encryption keys with documented access, rotation, and recovery procedures.

## 9. Observability and operations

- Measure load-balancer request success and latency; define SLO alerts, error-budget policy, and one-hour/six-hour burn-rate alerts.
- Dashboard regional health and failover, database status and lag, Cloud SQL storage/WAL, Datastream lag and slot retention, BigQuery freshness, per-zone capacity, pod placement, autoscaler state, IP use, quotas, and warm-region readiness.
- Alert before capacity exhaustion and before replication lag violates tested RPO or CDC freshness.
- Maintain runbooks for zone loss, regional recovery, promotion, restore/PITR, Datastream interruption, rollback, and fencing.

## 10. Testing and acceptance

- Before production, load-test peak traffic and validate pod sizing, database and read-replica capacity, autoscaler convergence, `/24` allocation assumptions, `/18` candidate ranges, quotas, reservations, IP capacity, surviving-zone capacity, and independent warm-region capacity.
- Perform quarterly zone-failure game days, including peak load and rollout conditions.
- Test drains and GKE upgrades with the selected PDB, placement rules, and surge settings.
- Rehearse regional recovery at least annually and record load-balancer failover, warm-capacity readiness, database promotion/fencing, endpoint switching, validation, CDC restart/catch-up, measured RTO, and RPO.
- Test restore/PITR at representative database sizes.
- Do not approve production launch until tests demonstrate the 99.95% service objective, no-intervention single-zone operation, and the measured regional RTO/RPO and CDC freshness objectives.

AGREE v3