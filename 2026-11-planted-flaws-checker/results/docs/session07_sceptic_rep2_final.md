# Highly available GKE platform with a Cloud SQL analytics feed: design v5

## 1. Targets and evidence gates

- The customer-facing web/API service has a 99.95% monthly end-to-end availability SLO, measured at the global load balancer. Dependency availability is tracked against this budget; individual dependency targets do not establish the end-to-end result.
- The service must continue serving without operator action after loss of one zone.
- Loss of the primary region requires rehearsed recovery in a warm second region, with target RTO 15 minutes and measured RPO 5 minutes.
- Peak traffic is approximately 5,000 requests/second. The team has eight engineers and prefers managed services.
- Before production approval, evidence must demonstrate at least 5,000 requests/second after loss of a zone; the regional RTO/RPO; replica lag supporting the RPO; restore/PITR performance; and CDC freshness and remediation behavior. These are evidence gates, not unmeasured guarantees.

## 2. Cluster, networking, and capacity

- Use regional GKE Standard clusters in europe-west2 and europe-west1, with control-plane and node capacity distributed across all three zones. Use separate system and application node pools, each with cluster autoscaling.
- Use VPC-native networking, private nodes, restricted control-plane access, and Cloud NAT. Document NAT capacity and regional failure behavior.
- Calculate each pod secondary range from GKE’s per-node allocation, maximum autoscaled node count, maximum pods per node, upgrade surge, and headroom. A /22 is not sufficient for 30 nodes at 110 pod IPs per node; reserve and test expansion capacity.
- Use the Regular GKE release channel, define maintenance windows, and validate upgrades outside production.
- The initial capacity hypothesis is approximately 800 requests/second per API pod; six pods provide only 4,800 requests/second and are not a design guarantee. Load-test with measured CPU, memory, downstream behavior, resource requests/limits, and failure headroom. Production replica count and reserved node capacity must support at least 5,000 requests/second after loss of any zone.
- Record node-pool minimums and maximums, zonal quota reservations, autoscaler reaction time, and surge capacity. Do not rely on reaching 90% utilization before recovering capacity.

## 3. Placement and disruption

- Run at least six replicas for stateless tiers, with topology spread constraints of `maxSkew: 1` and `whenUnsatisfiable: DoNotSchedule` across zones.
- Use required hostname anti-affinity only where the capacity model proves it will not prevent scheduling; otherwise topology spread is the placement guarantee.
- Configure PDBs to preserve the tested serving minimum while permitting at least one voluntary eviction. Do not set `minAvailable` to all six replicas.
- Use surge upgrades with documented `maxSurge` and `maxUnavailable`, compatible with node-pool capacity. Test draining, replacement scheduling, readiness, graceful termination, and load-balancer connection draining.

## 4. Warm regional recovery

- Maintain a warm recovery GKE Standard cluster in europe-west1 with the same three-zone topology, private VPC-native nodes, Cloud NAT, restricted control-plane access, quotas, node pools, and global-load-balancer integration.
- The enforceable initial warm minimum is **three system nodes, one per zone; six application nodes, two per zone; and nine application replicas, three per zone**, with pod capacity sufficient for those replicas. The application node-pool minimum, replica minimum, per-zone placement, and reserved zonal quotas must be configured before production. If load testing requires larger values, the larger tested values become the production minimum; failover must not depend on creating nodes or obtaining quota.
- Continuously replicate deployment manifests, images, configuration, secrets, certificates, firewall/network policy, and observability configuration. Test image availability and secret activation in europe-west1.
- Use a global external Application Load Balancer with healthy backends in both regions and health-based regional failover. DNS, including any 3,600-second TTL, is not part of regional failover.
- The timed recovery runbook is: within minutes 0–2 declare the incident and fence writes to the old primary; by minute 4 verify replica health and lag is within the five-minute RPO gate; by minute 7 promote the cross-region SQL replica; by minute 10 activate recovery configuration and secrets; by minute 12 validate readiness, reads, writes, and background jobs; and by minute 15 enable or confirm global-load-balancer cutover. Use fencing and generation/epoch checks to prevent split brain. Document rollback and measure every step. The complete sequence must be rehearsed at least annually.

## 5. Database

- Use Cloud SQL for PostgreSQL with regional HA enabled. The HA standby is for failover and is not a readable analytics endpoint.
- Provide analytics through a supported read replica or explicitly provisioned extraction path. Document lag, sizing, failure behavior, and whether reporting is degraded or stopped during failover.
- Maintain an asynchronous cross-region read replica in europe-west1. Continuously measure replication lag and alert before it threatens the five-minute RPO. Production approval requires measured lag within the RPO under normal and degraded load.
- Promotion requires replication-health checks, write fencing, prevention of old-primary writes, application connection changes, validation, and rollback considerations.
- Keep automated backups and PITR enabled. Measure restore and PITR objectives in a representative environment and state them as database-size- and workload-dependent objectives; do not claim a universal five-minute restore.

## 6. CDC and BigQuery

- Use Datastream with a supported Cloud SQL PostgreSQL configuration to read committed changes and write them to BigQuery. The freshness objective is five minutes, with alerting before breach and an explicit error budget.
- Every event contains an immutable event ID, source relation and key, operation (`insert`, `update`, or `delete`), source transaction/commit position or equivalent ordering value, and event version. Inserts and updates contain the resulting row image plus the changed-column metadata; deletes contain a tombstone with the key, version, and source ordering value.
- BigQuery application is idempotent. Deduplicate by event ID, apply only the greatest per-key version/source ordering value, and reject stale out-of-order events. Retries are safe. Inserts, updates, deletes, duplicates, out-of-order delivery, and replay are tested explicitly.
- Detect gaps using source transaction/sequence checkpoints and Datastream backlog/slot state. On a gap or prolonged stall, pause or bound ingestion, preserve the last checkpoint, repair by replaying the missing source range or resnapshotting the affected tables, reconcile counts/checksums, then resume from the repaired checkpoint. Record the procedure and its completion criteria.
- Monitor replication slots, WAL retention, primary storage, Datastream health, throughput, backlog, and end-to-end freshness. If Datastream stalls, use a bounded remediation procedure before WAL growth can endanger the primary.
- A 15-minute staleness limit must not conceal failure; it is only a separately defined degraded-service threshold consistent with the five-minute objective and alerts.

## 7. Security

- Use Workload Identity Federation for GKE, one appropriately scoped Google service account per tier, and no exported service-account keys.
- Deny cross-namespace traffic by default with network policies and allow only required flows.
- Use Binary Authorization so only approved pipeline-built images are admitted.
- Apply BigQuery policy tags to personal-data columns and customer-managed encryption keys where required. Document key availability, rotation, and recovery dependencies in both regions.

## 8. Observability, testing, and acceptance

- Measure request success rate and latency at the load balancer. Define SLO exclusions, burn-rate alerts, and dependency/error-budget reporting precisely.
- Monitor regional backend health and failover state, database and CDC lag, WAL retention, read-replica health, BigQuery freshness, node capacity by zone, quotas, autoscaler state, and failed scheduling.
- Conduct zonal-failure game days quarterly, regional recovery rehearsals annually, and node-upgrade/PDB disruption tests before production.
- Before build approval, record load-test results showing at least 5,000 requests/second after zone loss with resource and node details; pod-range calculations; quota and surge results; recovery-region minimum node/pod counts, per-zone distribution, and reserved quotas; timed recovery checkpoints completing within 15 minutes; measured restore and replica-lag results; and CDC stall, gap detection, replay, resynchronisation, idempotency, and freshness results.
- Every exercise produces a written report with findings, corrective actions, owners, and due dates.