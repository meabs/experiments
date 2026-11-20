# Highly available GKE platform with Cloud SQL analytics feed: design v3

## 1. Targets and acceptance criteria

- End-to-end customer availability SLO is 99.95% per calendar month, measured from global load-balancer logs for attempted valid application requests. An attempted valid application request is a request directed to the application service and not excluded by documented policy, whether or not it reaches the application backend. Intentional client cancellations, malformed requests, requests rejected by documented authentication/authorization policy, and traffic identified as synthetic tests are excluded. Server errors, dependency failures, timeouts, load-balancer errors, pre-backend failures, and incorrectly routed requests for attempted valid requests are included.
- The 99.95% SLO has a 0.05% monthly error budget. For internal operations, allocate that budget as follows: 0.010% load balancing/networking, 0.015% GKE/platform, 0.015% Cloud SQL and application dependencies, and 0.010% releases, recovery, and other operational activity. These are management budgets, not independent availability guarantees; the end-to-end SLO remains the governing objective.
- The service must continue serving through loss of any one zone without operator action.
- Regional recovery has an RTO of 15 minutes and an RPO of 5 minutes. These are acceptance criteria, not assumptions, and must be demonstrated in an annual recovery rehearsal.
- Peak traffic is 5,000 requests/second. Capacity tests must sustain at least 1.25 times peak with the largest planned node or zone failure.
- The platform consists of GKE, Cloud SQL, load balancing, and supporting managed services. Operational procedures must fit the eight-engineer team.

## 2. GKE cluster and networking

- Use one regional GKE Standard cluster in europe-west2, with the control plane and node pools distributed across all three zones.
- Use the Regular release channel (or Stable if required features are available there). Test upgrades in a representative environment before production maintenance.
- Use private nodes, authorised control-plane networks, VPC-native networking, and Cloud NAT. Monitor NAT port use, errors, and capacity.
- Size the Pod secondary range from the actual GKE alias-IP allocation model, `maxPodsPerNode`, maximum node count per zone, surge nodes, zone-loss rescheduling, and growth. Do not use a /22. Account for GKE per-node allocation blocks rather than only the number of running pod IPs. Validate that the range has capacity for the maximum autoscaled fleet plus upgrade surge and at least 30% growth; alert at 70% allocation. Size the node secondary range separately and document both calculations.
- Acceptance test: scale to the maximum planned node count plus surge and zone-loss rescheduling nodes while scheduling the configured maximum pods per node; no IP exhaustion or pending serving pods is permitted. Test exhaustion alerts and recovery.

## 3. Capacity and placement

- Run separate system and application node pools, each with cluster autoscaling and explicit minimum and maximum sizes in every zone.
- Six application replicas are the initial baseline. Load tests must demonstrate the stated per-pod throughput using production-equivalent resource limits, requests, HPA settings, startup/readiness probes, and dependencies, with headroom at 1.25 times peak.
- Use topology spread constraints across zones and required hostname anti-affinity where one replica per node is required. Verify placement after scale-up and node replacement.
- After a zone loss, the remaining zones must meet the tested capacity objective without operator action. The zone-loss test must leave at least 25% allocatable CPU and memory headroom after rescheduling serving pods and DaemonSets, accommodate planned surge, and produce zero pending serving pods. Autoscaler scale-up time is included in the test.

## 4. Disruptions and upgrades

- Use a PDB that permits planned maintenance while preserving the tested minimum service capacity; initial value is `minAvailable: 5` for six replicas, subject to load-test results. A PDB is not a substitute for spare capacity or zone-failure testing.
- Use surge upgrades with configured `maxSurge` and `maxUnavailable: 0`, after verifying that the pod range and node capacity accommodate surge nodes.
- Maintenance windows, rollout timeouts, readiness/startup probes, and rollback procedures are documented and tested.

## 5. Traffic and regional recovery

- Use a global external Application Load Balancer with backends in both regions and health checks that test application readiness and dependency health sufficiently to prevent routing to an unable-to-serve backend.
- Do not depend on a 3,600-second DNS TTL for failover. Client traffic steering uses load-balancer health-based backend failover. Any DNS used for application endpoints has a documented low TTL, but recovery testing must account for resolver and client caching.
- Region two has a continuously deployable application environment matching configuration, secrets, image versions, capacity, and network policy. It must be capacity-tested independently at 1.25 times peak, or 6,250 requests/second, with production-equivalent limits, autoscaling, dependencies, and the promoted database configuration.
- Regional recovery runbook: detect and declare the incident; fence writes and prevent the old region from accepting writes; confirm replica lag and the chosen recovery point; promote the cross-region Cloud SQL replica; update application database endpoints/secrets; enable the region-two backend; validate writes and reads; reconfigure and validate Datastream; then route traffic and monitor.
- Fencing must be tested, including loss of connectivity and stale application instances, to prevent split-brain writes. Recovery must not claim success until the old region cannot write.
- Acceptance test: from fault injection through detection, fencing, promotion, endpoint/configuration switching, Datastream recovery, traffic steering, and customer request success, complete within 15 minutes. Region two must sustain 6,250 requests/second under the planned failure assumptions. Record each timestamp, resolver/cache behavior, and achieved RPO. The promoted replica must be no more than five minutes behind at the recovery point; otherwise the runbook declares the RPO unmet and records the data-loss consequence. This is a go/no-go test.

## 6. Cloud SQL

- Use Cloud SQL for PostgreSQL HA with automatic regional failover for normal zonal failures. HA standby storage is not used for reporting queries.
- Provide a separately provisioned, supported read replica for analytics, with capacity sized for dashboard load. Monitor replica lag and define behavior when lag exceeds the reporting freshness objective; dashboards may be degraded or paused rather than overload the primary.
- Maintain an asynchronous cross-region read replica for disaster recovery. Measure replication lag continuously and alert before the five-minute RPO boundary. Test promotion, connection changes, permissions, extensions, and application compatibility.
- Automated backups and point-in-time recovery remain enabled. Backup retention, encryption, and restore permissions are documented.
- Restore RTO is measured using a production-sized database and growth projections. Quarterly restore tests must record backup selection, restore duration, validation duration, and resulting RPO. The measured restore duration plus agreed operational margin is the corruption-recovery objective. The measured result is a go/no-go criterion: it must meet the approved corruption-recovery RTO, or launch is blocked or an explicitly approved exception is recorded.

## 7. Datastream and BigQuery

- Datastream reads committed changes from PostgreSQL using a supported logical-decoding configuration and writes to BigQuery. Configure and monitor replication slots, WAL retention, slot restart LSN, primary storage, stream errors, and backpressure.
- A lag or stream outage must not allow unbounded WAL growth or threaten the primary. Define a threshold that pauses or limits ingestion, pages an engineer, and recovers or reinitializes the stream before primary storage is endangered.
- The committed-change freshness objective is five minutes, measured from commit time to queryable BigQuery availability. Alert at three minutes and page at five minutes. BigQuery’s 15-minute staleness setting is not evidence that this objective is met.
- Use an idempotent event identity and merge strategy, with replay handling and reconciliation counts. Validate duplicates, retries, schema changes, failover, stream restart, and regional promotion without lost committed changes, incorrect rows, unbounded duplication, or WAL exhaustion.
- Acceptance testing at peak-rate change traffic must show at least 99% of sampled committed changes queryable within five minutes, including outage, backpressure, promotion, slot reconfiguration, and recovery tests.

## 8. Security

- Use Workload Identity Federation for GKE, one least-privilege Google service account per tier, and no exported keys.
- Deny cross-namespace traffic by default with NetworkPolicies. Binary Authorization admits only images built and signed by the approved pipeline.
- Apply BigQuery policy tags to personal data and use customer-managed encryption keys with tested rotation and recovery procedures.

## 9. Observability and operations

- SLIs are load-balancer request success rate and latency, plus database failover health, read-replica lag, cross-region lag, CDC commit-to-query freshness, WAL/slot retention, node capacity by zone, autoscaler state, and load-balancer backend health.
- Alert on fast and slow error-budget burn, zone capacity loss, database and CDC thresholds, and impending IP/WAL/storage exhaustion.
- Run a zone-failure game day at least quarterly, a backup restore test quarterly, and a full regional recovery rehearsal annually. Each produces a report with measured availability impact, RTO, RPO, lag, fencing results, CDC recovery, and corrective actions.
- No production launch is approved until the pod-range, capacity, zone-loss, region-two 6,250-request/second, restore, CDC, and regional recovery acceptance tests pass or have explicitly approved exceptions.