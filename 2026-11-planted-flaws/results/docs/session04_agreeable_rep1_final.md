# Highly available GKE platform with a Cloud SQL analytics feed: design v2

## 1. Targets and availability

- Customer-facing stateless web/API service, with peak traffic of approximately 5,000 requests/second.
- Platform SLO: 99.95% monthly availability, measured by successful and timely requests at the load balancer. The error budget is approximately 22 minutes per month.
- The availability model explicitly includes GKE, Cloud SQL, load balancing, networking, application dependencies, and regional recovery procedures. Individual managed-service targets do not automatically compose to the platform SLO; dependency failures consume the common error budget.
- The platform survives loss of one zone without operator action.
- Regional loss is handled by a documented and rehearsed recovery in europe-west1, with a 15-minute RTO and a five-minute operational RPO target. The RPO is measured and monitored, not assumed or guaranteed.
- The team is eight engineers and uses managed services wherever practical.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across three zones and node pools distributed across all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled.
- The pod secondary range is sized from the maximum node count, GKE per-node allocation behavior, post-zone-loss scaling requirement, and growth allowance. The original /22 is not sufficient; the selected range (initially expected to be approximately /18 or larger) must be validated before build.
- The cluster uses VPC-native networking and private nodes. Control-plane access is restricted to authorized networks.
- Internet egress uses Cloud NAT with sufficient capacity and regional quota. NAT capacity, port exhaustion, and failure behavior are monitored.
- Use the GKE Regular release channel for production, with a tested maintenance policy and a weekly maintenance window on Sunday from 02:00 to 06:00 local time.

## 3. Capacity

- Each API pod is currently estimated to serve approximately 800 requests/second. Six replicas provide capacity above the 5,000-request/second peak; this estimate is validated with load tests.
- Capacity planning includes normal peak traffic, loss of one zone, autoscaler reaction time, regional quotas, and node startup time.
- Each zone is sized for approximately 60% utilization at peak under normal conditions. After loss of one zone, the remaining zones and autoscaler must be demonstrated to sustain the required service level; the previously stated 90% figure is a test target, not an assumption.

## 4. Workload placement and disruption

- Stateless tiers run six replicas with topology spread constraints across zones (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Preferred hostname anti-affinity is used to reduce same-node concentration; capacity and spread constraints are validated during scale-out and failure tests.
- Each tier has a disruption budget that permits voluntary maintenance while preserving service, initially `minAvailable: 5` for six replicas. The value is reviewed against load-test results and zone-loss requirements.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to sufficient spare capacity and quota.
- Zone-loss and node-drain game days verify that scheduling, autoscaling, PDBs, and capacity work together.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use an application health endpoint that reflects readiness for serving traffic.
- Regional traffic shift uses the load balancer's health-based failover or traffic steering, not a 3,600-second DNS failover. Any DNS used for service discovery has a tested TTL and documented resolver-cache behavior.
- Regional recovery is a single runbook coordinating:
  1. write protection or application quiescing in the failed region;
  2. verification of cross-region Cloud SQL replica lag;
  3. promotion of the europe-west1 replica;
  4. configuration of the application to use the promoted database;
  5. global load-balancer traffic shift;
  6. validation of service, writes, and CDC; and
  7. rollback or restoration of the original region when safe.
- The runbook records measured promotion, traffic-convergence, and application-recovery times. It includes explicit RPO bounds, rollback steps, and operator ownership.
- The regional recovery rehearsal is performed at least annually and after material architecture changes.

## 6. Database

- Cloud SQL for PostgreSQL uses regional high availability, with a primary and failover standby in separate zones. The HA standby is not used for reads.
- Analytics dashboards use a separately provisioned and sized Cloud SQL read replica, preferably in-region, with replication-lag, capacity, and availability monitoring. If it lags or fails, dashboards degrade or become unavailable rather than querying the transactional primary.
- A cross-region read replica in europe-west1 is the regional-recovery target. Replica lag is continuously monitored and alerted before it exceeds the five-minute operational RPO bound.
- Promotion prerequisites, application connection changes, write protection, and rollback are documented and tested.
- Automated backups and point-in-time recovery are enabled. Restore objectives are size-dependent measured targets, not a claim of five minutes regardless of database size. Backup restore and PITR are tested regularly.
- A bad migration has a documented recovery procedure, including decision criteria for rollback versus PITR and its effect on RPO/RTO.

## 7. Change data capture to BigQuery

- Datastream reads Cloud SQL changes through supported PostgreSQL logical-decoding configuration and writes them to BigQuery.
- Replication slots, WAL retention, source storage impact, Datastream health, and replication lag are monitored. Alerts and runbooks prevent CDC lag from endangering primary storage.
- The target is for every committed change to reach BigQuery within approximately five minutes. Freshness alerts fire before that objective is missed.
- BigQuery table/query freshness and staleness settings are configured consistently with the five-minute requirement; a 15-minute staleness limit is not used as the stated freshness objective.
- Event application is idempotent, using primary-key merges or an equivalent deduplication strategy.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default.
- Binary Authorization admits only images built and signed by the approved pipeline.
- Personal-data columns use BigQuery policy tags, and datasets use customer-managed encryption keys.

## 9. Observability and operations

- SLIs are load-balancer request success rate and latency, with one-hour and six-hour error-budget burn-rate alerts.
- Dashboards cover application capacity, zonal node capacity, autoscaler state, Cloud NAT utilization, quotas, Cloud SQL HA and read-replica lag, cross-region replica lag, Datastream freshness and slot/WAL retention, and BigQuery freshness.
- Runbooks cover zonal failure, node maintenance, analytics-replica failure, CDC lag, database promotion, regional recovery, and backup restoration.
- Alerts have assigned owners and tested escalation paths.

## 10. Validation and testing

Before production, the team validates:

- pod-range sizing and IP allocation;
- autoscaler behavior, node quotas, surge upgrades, and post-zone-loss capacity;
- Cloud NAT capacity and failure behavior;
- application load and reduced-capacity performance;
- Cloud SQL failover, read-replica isolation, cross-region lag, promotion, and rollback;
- Datastream logical-decoding prerequisites, lag, slot/WAL protection, and BigQuery freshness;
- global load-balancer regional failover and convergence;
- backup/PITR restore time at representative database sizes; and
- end-to-end SLO measurement and dependency/error-budget accounting.

A zone-failure game day runs quarterly. A full regional recovery rehearsal runs annually, with written results, measured RTO/RPO, identified corrective actions, and revalidation after remediation.