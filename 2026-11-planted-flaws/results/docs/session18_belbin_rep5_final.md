# Highly available GKE platform with a Cloud SQL analytics feed: design v2

## 1. Targets and service objectives

- Customer-facing stateless web/API service target: 99.95% monthly availability, measured at the global load balancer. The end-to-end SLO and error budget will account for serial dependencies rather than assuming component availabilities combine to 99.95%.
- Peak traffic is approximately 5,000 requests/second. Capacity targets include headroom for bursts, maintenance, and loss of one zone.
- The platform must tolerate loss of one zone without operator action.
- Regional loss has a documented, rehearsed recovery with a 15-minute RTO and a 5-minute RPO objective. The achievable RPO is bounded by measured cross-region Cloud SQL replica lag and is alerted when approaching five minutes.
- The team is eight engineers using managed services.

## 2. GKE topology and capacity

- Use a regional GKE Standard cluster in europe-west2, with a replicated control plane and node pools across all three zones.
- Use separate system and application node pools, cluster autoscaling, and sufficient per-zone spare capacity.
- Use the Regular GKE release channel (or Extended where justified), with compatibility testing, a documented upgrade policy, and a tested maintenance window.
- Use private nodes, authorized control-plane networks, VPC-native networking, and regional Cloud NAT.
- Size pod secondary ranges from the configured `maxPodsPerNode`, maximum node count in all pools, surge nodes, system-pod allocation, and growth headroom. Validate IP capacity before build; do not assume a /22 is sufficient.
- Provision the secondary region with replicated configuration, images, secrets, networking, and enough tested GKE capacity for regional recovery. Its capacity and readiness are monitored.

## 3. Workload placement and disruption

- Stateless tiers run at least seven replicas, or another performance-tested count that provides validated headroom above 5,000 requests/second. The stated six replicas at 800 requests/second is insufficient.
- Size each zone so the remaining two zones can serve peak traffic plus burst, maintenance, and autoscaler headroom after one-zone loss. Validate this with load and failure tests.
- Use topology spread constraints across zones. Use required hostname anti-affinity when one replica per node is required; otherwise document the permitted fallback and verify capacity.
- Use a PodDisruptionBudget such as `minAvailable: 5` for seven replicas, adjusted per tier after testing, so voluntary maintenance can proceed while preserving the availability objective.
- Use node-pool surge upgrades with tested surge and spare-capacity settings. PDBs must not be used as a substitute for capacity.

## 4. Traffic and regional failover

- Use a global external Application Load Balancer with backends in both regions and health-based regional failover. Do not depend on a 3,600-second DNS TTL for the regional RTO.
- Health checks must represent serving readiness, not merely process liveness. Configure and test connection draining and failover behavior.
- The recovery runbook includes secondary-region activation, application configuration and secret availability, Cloud SQL promotion, connection cutover, and verification that failover completes within 15 minutes.

## 5. Cloud SQL and recovery

- Use Cloud SQL for PostgreSQL with regional HA and automatic zonal failover.
- Do not use the HA standby for reporting. Provision a separately supported read replica for analytics, size it for dashboard load, and monitor lag, health, and failover behavior.
- Maintain a cross-region read replica in europe-west1 for disaster recovery. Alert on replica lag and promotion readiness; rehearse promotion and application connection switching. The measured lag determines the actual bounded RPO, with an objective of five minutes.
- Automated backups and point-in-time recovery remain enabled. Replace the unconditional five-minute restore claim with size-dependent, measured restore objectives, including backup validation and migration rollback procedures.
- Regional recovery testing records promotion time, replica lag/data loss, restore time where applicable, and application cutover time.

## 6. Datastream and BigQuery

- Configure and validate PostgreSQL logical decoding prerequisites and permissions.
- Monitor Datastream health, replication-slot retention, WAL growth, primary storage, source impact, destination freshness, and restart/replay behavior.
- Alerts must prevent CDC lag or a stalled slot from exhausting primary storage; define an operational response, including pausing or safely resynchronizing the stream where necessary.
- Configure idempotent destination processing so retries and duplicate events do not create duplicate rows.
- The committed-change requirement is five minutes: alert before that bound is breached and set the BigQuery freshness/staleness policy accordingly. A 15-minute staleness limit is not sufficient unless explicitly shown not to govern freshness or the requirement is renegotiated.
- Document Datastream behavior during Cloud SQL failover and regional promotion, including restart and reconciliation.

## 7. Security and observability

- Use Workload Identity Federation for GKE, one Google service account per tier, network policies denying cross-namespace traffic by default, and Binary Authorization for pipeline-built images.
- Protect personal-data columns with BigQuery policy tags and use customer-managed encryption keys.
- Measure load-balancer success rate and latency for SLIs. Alert on one-hour and six-hour error-budget burn rates.
- Dashboard request/error and latency SLOs, per-zone capacity, autoscaler state, GKE upgrade status, Cloud SQL HA and replica lag, Datastream lag/WAL retention/storage risk, BigQuery freshness, and regional failover readiness.

## 8. Testing and operational readiness

- Run a quarterly zone-failure game day and an annual full regional recovery rehearsal, each with a written report and remediation tracking.
- Before production, load-test the validated replica count and per-pod capacity, test one-zone loss at peak load, test node upgrades and PDB behavior, verify IP and autoscaler limits, and exercise global-load-balancer failover.
- The regional rehearsal must demonstrate the 15-minute RTO and five-minute RPO objective (or document the measured limitation), including Cloud SQL promotion, application cutover, Datastream resumption, and BigQuery freshness recovery.