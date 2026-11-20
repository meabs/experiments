# Highly available GKE platform with a Cloud SQL analytics feed: design v2

Written by Agent I, platform lead.

## 1. Targets

- End-to-end service availability SLO: 99.95% per month, measured at the load balancer. Dependencies and their failure modes are included in this budget; individual managed-service targets are not multiplied to claim the composite SLO.
- Survive loss of one zone without intervention.
- Survive loss of a region through a documented, rehearsed recovery in a second region, with a tested RTO of 15 minutes and RPO of 5 minutes.
- Peak traffic is approximately 5,000 requests per second. The design remains within an eight-engineer managed-service operating model.
- Every committed change must reach BigQuery within 5 minutes. A 15-minute BigQuery destination staleness setting is not used as the freshness SLO.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across three zones and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled.
- The cluster uses VPC-native private nodes and authorised control-plane networks. Internet egress uses Cloud NAT through a regional Cloud Router.
- The pod secondary range is sized from the maximum node and pod plan, including growth and upgrade headroom; `/22` is insufficient. The final CIDR is recorded in the capacity plan before build.
- Use the Stable GKE release channel, with a tested maintenance window and upgrade policy.

## 3. Capacity

- The API tier starts with at least seven replicas. Six replicas at 800 requests per second would provide only 4,800 requests per second and is insufficient before headroom.
- Load tests validate throughput, CPU and memory limits, node capacity, database capacity, and adequate headroom at the 5,000-request-per-second peak.
- Node pools are distributed across all zones and sized so that loss of one zone remains within tested capacity. Autoscaling limits, scale-up time, and post-failure utilization are tested and documented.

## 4. Workload placement and disruption

- Stateless tiers use at least seven replicas where required by capacity, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Required anti-affinity or equivalent placement rules prevent avoidable same-node concentration; placement is verified in tests.
- Each tier uses a workable PodDisruptionBudget, initially `minAvailable: 5` for a seven-replica tier, adjusted per tier based on its capacity test. Budgets must permit controlled maintenance while preserving service and zone resilience.
- Node pools use surge upgrades with `maxUnavailable: 0` and tested surge capacity.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use an application health endpoint that reflects serving readiness, and connection draining is 60 seconds.
- Regional recovery uses the load balancer’s tested health-based backend failover, not reliance on a 3,600-second DNS change. Any DNS used for administration has a low, documented TTL, with resolver-caching limitations recorded.
- The recovery runbook, rehearsed against the 15-minute RTO, is: declare the regional incident; promote the cross-region database replica; switch the application’s database endpoint; validate data consistency, CDC continuity, and observed replication lag against the 5-minute RPO; verify the standby region; then shift traffic and monitor.

## 6. Database

- Cloud SQL for PostgreSQL in europe-west2 uses high availability, with automatic failover between zones. Automated backups and point-in-time recovery are enabled.
- Analytics reads from a supported dedicated read replica or reporting replica, never from the HA standby. Replica capacity, lag, and failure behavior are monitored.
- A cross-region read replica in europe-west1 is the regional-recovery target and is promoted by the documented runbook. Cross-region replication is asynchronous; observed lag is measured continuously and during rehearsals to substantiate the 5-minute RPO.
- Backup restore objectives are size-dependent, measured, and rehearsed. The design makes no unconditional five-minute restore claim.

## 7. Change data capture to BigQuery

- Datastream uses a supported Cloud SQL PostgreSQL logical-decoding configuration and reads changes without endangering primary performance.
- Replication slots, WAL/storage growth, primary impact, backpressure, and lag are monitored, with operational limits and escalation procedures.
- The freshness SLO is that committed changes reach BigQuery within 5 minutes; alerting and escalation occur at the threshold. Duplicate events are handled idempotently, such as by merge on the primary key.
- CDC continuity and freshness are explicitly validated during regional recovery before traffic is shifted.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only pipeline-built images.
- Personal-data columns use BigQuery policy tags, and datasets use customer-managed encryption keys.

## 9. Observability

- SLIs are load-balancer request success rate and latency. Alerts use one-hour and six-hour error-budget burn rates.
- Dashboards and alerts cover replica and CDC lag, BigQuery freshness, WAL/slot health, node capacity by zone, autoscaler state, load-balancer backend health, and recovery-runbook milestones.
- Recovery rehearsals record observed RTO, RPO/replica lag, CDC freshness, and traffic-shift results.

## 10. Testing

- Perform a zone-failure game day quarterly and a full regional recovery rehearsal annually, each with a written report.
- Before production, load-test peak traffic and one-zone loss, test rolling upgrades and disruption budgets, measure database restore and promotion times, validate CDC primary impact and freshness, and demonstrate the 15-minute RTO and 5-minute RPO.