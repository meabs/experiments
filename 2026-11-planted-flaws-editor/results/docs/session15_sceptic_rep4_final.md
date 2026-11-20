# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets and acceptance criteria

- The customer-facing service has a 99.95% monthly end-to-end availability SLO, measured at the global load balancer. The error budget is approximately 22 minutes per month.
- Availability is modelled end to end, including load balancing, GKE, Cloud SQL, networking, deployments, and regional failover. Individual component availability figures are not added or treated as sufficient evidence of the platform SLO.
- The service must continue operating without operator action after loss of any one zone.
- Regional recovery has a 15-minute RTO and a five-minute RPO. These are acceptance criteria demonstrated in rehearsals, not assumptions derived solely from service configuration.
- Peak traffic is approximately 5,000 requests per second. The platform is operated by eight engineers using managed services.

## 2. GKE topology and capacity

- The primary cluster is a regional GKE Standard cluster in `europe-west2`, with a control plane replicated across its three zones and node pools distributed across all three zones.
- A recovery-region GKE cluster is provisioned in `europe-west1`, with the production configuration and application images continuously deployed. It has capacity for the tested peak workload without depending on node creation during an incident; autoscaling is used only for additional demand.
- System and application node pools are separate. Resource requests, quotas, startup times, autoscaler limits, and per-zone capacity are recorded and tested.
- The cluster is VPC-native with private nodes. Control-plane access is restricted to authorised networks. Internet egress uses Cloud NAT.
- The pod secondary range is selected only after documenting the actual per-node Pod CIDR allocation, maximum nodes, upgrade surge, and growth headroom; its size is validated before build approval. The recovery cluster’s pod range is sized by the same method. The range is not sized from workload replica count alone.
- The cluster uses the Regular release channel, or Stable if required features are supported there, after compatibility testing. A tested maintenance window and upgrade rollback procedure are maintained.

## 3. Application capacity and placement

- Capacity tests establish the number of replicas and CPU/memory requests needed for 5,000 requests per second. Six replicas are used initially only if testing confirms their capacity and failure margins.
- Each zone is provisioned with sufficient spare capacity to absorb the loss of one zone at the required service level. This includes node startup, quotas, and scheduling time; autoscaler reaction is not treated as the zone-loss guarantee.
- Stateless tiers use topology spread constraints across zones. Required hostname anti-affinity is used where one replica per node is required; otherwise the placement guarantee is explicitly documented and tested.
- Each tier has a PodDisruptionBudget permitting at least one voluntary disruption (initially `minAvailable: 5` for six replicas), while preserving the tested serving capacity. PDB behavior is tested during drains and upgrades.
- Node pools use surge upgrades with settings validated against available spare capacity. Upgrade completion and rollback are tested.

## 4. Traffic and regional failover

- Traffic enters through a global external Application Load Balancer with backends in both regions.
- Regional backend health checks use a readiness endpoint that verifies the dependencies required to serve traffic, rather than merely proving that the process is running. Liveness and readiness checks are separate.
- Regional failover uses the load balancer's tested health-based failover. DNS changes are not part of the 15-minute RTO mechanism, and no 3,600-second DNS TTL is relied upon.
- Connection draining, retry behavior, and client-visible failover are tested end to end. The regional recovery rehearsal measures detection, draining, application readiness, database promotion, write fencing, and restoration of writes.

## 5. Cloud SQL

- The transactional PostgreSQL database is Cloud SQL HA in `europe-west2`, with automated backups and point-in-time recovery enabled. The HA standby is used for failover only and is not used as a reporting endpoint.
- Analytics dashboards use a separately provisioned, supported Cloud SQL read replica (or an explicitly approved alternative export path). Its capacity, lag, failover behavior, and dashboard query load are monitored.
- A cross-region read replica in `europe-west1` is continuously monitored for replication lag and WAL retention. The runbook records measured promotion time, possible data loss, application connection cutover, and the conditions under which the five-minute RPO is achieved.
- Regional recovery includes write fencing of the old primary, promotion of the replica, validation of the promoted database, application cutover, and split-brain prevention. Promotion is not described as lossless unless testing proves that.
- Backup restore and point-in-time recovery times are measured using production-sized data and documented by database size. No fixed restore time is assumed. Restore validation includes integrity checks and application smoke tests.

## 6. CDC and BigQuery

- Datastream reads changes from the Cloud SQL primary using a supported logical-decoding configuration and is monitored for source impact, errors, backlog, and end-to-end freshness.
- The objective is that every committed change is queryable in BigQuery within five minutes under normal conditions. Alerts measure commit-to-queryable latency, with a warning before five minutes and a critical alert at the objective.
- BigQuery configuration must not permit a 15-minute staleness limit to mask violation of the five-minute delivery objective; cost controls are implemented without weakening that objective.
- Loads are idempotent and tested for duplicate, delayed, reordered, and replayed events. Merge keys and any required ordering/version columns are defined.
- The regional recovery runbook documents Datastream checkpoint handling, restart and replay behavior, duplicate prevention, and reconciliation after database promotion.

## 7. Security

- Workloads use Workload Identity Federation for GKE, with one least-privilege Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only images built and signed by the approved pipeline.
- Personal-data columns use BigQuery policy tags. Datasets use customer-managed encryption keys with documented key availability and rotation procedures.

## 8. Observability and operations

- SLIs are load-balancer request success rate and latency, with alerts for one-hour and six-hour error-budget burn.
- Dashboards include per-zone capacity, scheduling failures, autoscaler state, node startup time, load-balancer backend health, Cloud SQL replication and promotion metrics, read-replica lag, Datastream lag, and end-to-end BigQuery freshness.
- Alerts exist for loss of the five-minute RPO condition, excessive cross-region replica lag, CDC backlog, and failure of write fencing.
- Runbooks cover zone loss, regional failover, database promotion, fencing, split-brain prevention, rollback, CDC replay, and restoration of normal topology.

## 9. Testing and approval gates

- Before production, load and failure tests demonstrate 5,000 requests per second capacity, one-zone survival, upgrade/drain behavior, global load-balancer failover, and recovery-region capacity.
- A quarterly zone-failure game day and an annual full regional recovery rehearsal produce written results and corrective actions.
- Production approval requires measured evidence for the end-to-end SLO model, regional RTO, achievable RPO, database promotion and restore times, CDC recovery, and idempotent BigQuery replay.