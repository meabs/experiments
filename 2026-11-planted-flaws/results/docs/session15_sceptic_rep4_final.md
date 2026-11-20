# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets and assumptions

- The customer-facing stateless web/API service has a 99.95% monthly availability SLO, with an explicit end-to-end availability model and error budget covering application, GKE, database, load balancing, dependencies, and failover operations. Individual service availability figures are not summed to justify the platform SLO.
- Peak traffic is approximately 5,000 requests/second. Capacity targets include headroom and are validated by load tests.
- The primary deployment is in europe-west2 and must tolerate loss of one zone without operator action.
- Regional loss has a documented and rehearsed recovery in europe-west1. The measured RTO target is 15 minutes and the measured RPO target is 5 minutes; these are not assumed guarantees.
- The team is eight engineers and uses managed services where practical.

## 2. GKE topology and networking

- Use one regional GKE Standard cluster in europe-west2, with nodes distributed across all three zones. Use separate system and application node pools, both with cluster autoscaling.
- Use the Regular release channel (or Stable if its required features are available), after compatibility testing. Define a maintenance window and test upgrades before production rollout.
- The cluster is VPC-native with private nodes and a restricted control-plane endpoint. Internet egress uses Cloud NAT with monitored capacity and a documented regional failure posture.
- Size the Pod secondary range from the maximum autoscaled node count, configured `maxPodsPerNode`, GKE alias-IP per-node allocation, upgrade surge, zone-loss scenario, and growth headroom. Do not use `/22` as the current design assumption. Reserve a sufficiently large range (initial sizing, subject to the GKE calculator and quota review, is `/18`) and verify expansion procedures.
- Validate subnet, secondary-range, quota, NAT, and startup capacity in a zone-loss and upgrade-scale test.

## 3. Capacity and scaling

- Performance testing must establish per-pod throughput, CPU/memory limits, latency, and behavior under realistic traffic. At 800 requests/second per pod, six replicas provide only 4,800 requests/second, so deploy at least seven replicas for the stated peak before additional headroom; the final replica count must come from testing.
- Use horizontal pod autoscaling based on measured CPU and/or request/concurrency metrics, with minimum replicas and maximum replicas sufficient for peak, burst, and zone-loss recovery.
- Size each zone and the autoscaler maximum for system pods, DaemonSets, application pods, node replacement, surge upgrades, and loss of one zone. Demonstrate acceptable utilization and startup time after a zone loss; do not rely on an unvalidated 90% figure.

## 4. Workload placement and disruption

- Run at least the tested minimum replica count, spread across zones with required topology constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`) and required hostname separation where one replica per node is a requirement. Preferred anti-affinity alone is not a guarantee.
- Configure PodDisruptionBudgets to permit controlled voluntary maintenance while preserving the tested serving and zone-failure capacity (for example, `minAvailable: replicas - 1`, subject to load and upgrade testing). Do not set a budget equal to all replicas unless blocking maintenance is intentional.
- Use surge upgrades with tested spare node, quota, IP, and capacity headroom. Verify that drains and upgrades complete without violating the service SLO.

## 5. Traffic and regional recovery

- Use a global external Application Load Balancer with independently health-checked backends in both regions. Health checks must represent application readiness and database/write state, not merely process liveness. Configure connection draining and test regional backend failover.
- The europe-west1 recovery backend must have explicitly provisioned, tested serving capacity: a warm or reproducibly deployable GKE cluster, node pools and autoscaler limits, Pod secondary ranges, quotas, images, secrets, configuration, and required dependencies. If scaled down, its startup and scaling time must be measured. It must be capable of serving the tested peak workload after europe-west2 loss; creating unvalidated capacity during the incident is not an acceptable recovery assumption.
- Do not depend on a 3,600-second DNS TTL for a 15-minute RTO. Client traffic failover uses the load balancer's health-based routing. Any DNS used for administrative or alternate endpoints has a bounded, tested TTL.
- The regional recovery runbook includes declaring the incident, fencing writes to the failed region, promoting the europe-west1 Cloud SQL replica, updating application configuration/secrets and write endpoints, starting or scaling the provisioned europe-west1 GKE workload, validating backend health, routing traffic, smoke-testing reads and writes, reconciling CDC, and communicating any data loss. Promotion, workload startup, traffic cutover, and application validation are timed in rehearsals.

## 6. Cloud SQL

- Cloud SQL for PostgreSQL HA remains the transactional primary in europe-west2, with automatic zonal failover, automated backups, and point-in-time recovery.
- The HA standby is not a reporting endpoint. Dashboards use a separately sized, supported read replica or another explicitly supported analytics path. Monitor replica lag, capacity, query impact, and failure behavior.
- A cross-region asynchronous read replica in europe-west1 is the regional recovery target. Monitor replication lag and alert before the five-minute RPO objective is breached. The promotion point and acceptable data-loss behavior are explicit in the runbook.
- Backup restore time is database-size and workload dependent. Remove any unconditional five-minute claim. Establish restore and promotion RTOs with representative, recurring drills and document measured results.
- Test recovery from bad migrations using point-in-time restore, including application compatibility and rollback/fencing procedures.

## 7. CDC to BigQuery

- Configure and validate Datastream using the supported Cloud SQL PostgreSQL logical-decoding prerequisites, least-privilege access, replication-slot management, and WAL retention limits.
- Target committed-change freshness is approximately five minutes, with alerts at three minutes. Monitor source impact, slot lag, WAL/storage growth, Datastream backlog, errors, and BigQuery ingestion latency. Define throttling, pause, and recovery procedures so CDC cannot exhaust primary storage.
- Validate initial backfill, ordering, deletes, updates, duplicates, retries, schema changes, failover, and regional recovery. The BigQuery apply process must be idempotent and preserve the required change semantics; a primary-key merge alone is not sufficient.
- Set the BigQuery staleness and cost policy only after confirming it is compatible with the five-minute freshness requirement.
- Reconcile and replay events generated or in flight during regional promotion and application cutover, with documented duplicate and ordering handling.

## 8. Security

- Use Workload Identity Federation for GKE with a dedicated Google service account per tier and no exported keys.
- Apply default-deny network policies between namespaces, and use Binary Authorization for images built by the approved pipeline.
- Protect personal-data columns with BigQuery policy tags and use customer-managed encryption keys, with documented key rotation and recovery procedures.

## 9. Observability and operations

- Measure request success rate and latency at the load balancer and application layers. Alert on one-hour and six-hour error-budget burn, database health, replica lag, CDC freshness, WAL/storage pressure, node and IP capacity, autoscaler state, quota exhaustion, and regional backend health.
- Define ownership, escalation, and runbooks for zonal failure, database failover, CDC degradation, and regional recovery.
- Record measured RTO/RPO, replica lag at promotion, lost transactions if any, workload startup time, traffic-cutover time, and validation results from every rehearsal.

## 10. Testing and acceptance

- Before production, run load and soak tests at peak plus headroom; zone-failure tests; node-drain and upgrade tests; database failover and restore tests; CDC replay/backfill/failure tests; and global load-balancer regional-failover tests.
- Conduct a zone-failure game day at least quarterly and a full regional recovery rehearsal at least annually, each with written findings and tracked remediation.
- The regional rehearsal must demonstrate that the provisioned or reproducibly deployable europe-west1 GKE capacity, quotas, IP ranges, images, secrets, autoscaling, database promotion, CDC reconciliation, and load-balancer cutover can serve the tested workload within the measured 15-minute RTO.
- Build approval requires evidence that capacity, IP ranges, quotas, upgrade operations, the five-minute CDC freshness objective, and the measured regional RTO/RPO meet the stated objectives.