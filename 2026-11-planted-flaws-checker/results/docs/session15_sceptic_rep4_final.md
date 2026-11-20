# Highly available GKE platform with Cloud SQL analytics feed: design v5

## 1. Targets and assumptions

- Customer-facing stateless web/API service, peak 5,000 requests/second.
- Monthly end-to-end availability SLO is 99.95% (about 22 minutes of error budget). This covers successful, appropriately latent user requests, including GKE, load balancing, Cloud SQL, networking, DNS/client behavior, deployments, and operational failover. Dependency incidents and client-visible failover time count against it. Planned maintenance is excluded only where the SLO contract explicitly permits it and remains within the documented budget.
- The primary region is europe-west2; the recovery region is europe-west1. A complete, runnable GKE deployment and load-balancer backend exists in both regions. The recovery region has capacity for the tested recovery workload.
- Automatic recovery from loss of one zone is required. Regional recovery is documented and rehearsed with RTO 15 minutes and an explicitly accepted worst-case RPO of five minutes, subject to the replica-lag gate.
- All objectives are tested before production.

## 2. GKE topology and networking

- Each region has a private, VPC-native GKE Standard cluster with nodes distributed across three zones. The primary is regional; the recovery cluster is maintained sufficiently to receive production traffic and has tested capacity.
- System and application node pools are separate, with autoscaling and quotas sized for normal load, one-zone loss, node replacement, and upgrade surge. Each surviving zone has spare capacity to absorb the lost zone and maintenance surge; this is verified in a zone-loss game day.
- Pod secondary ranges are calculated, not assumed. Required `/24` blocks equal the maximum concurrent nodes across application and system pools, plus replacement and upgrade-surge nodes, plus an explicit growth reserve. The illustrative 30-node example is not a provisioning decision and excludes no category implicitly; unless explicitly recalculated, it must not be treated as including system nodes, replacement nodes, surge, or growth. The final CIDR is selected from the calculation and validated against `maxPodsPerNode`, GKE per-node Pod CIDR allocation, maximum autoscaled nodes, system pods, surge behavior, and growth plan before creation. Pod-range exhaustion and surge scheduling are acceptance-tested.
- Nodes are private. Control-plane access is restricted to authorised networks.
- Each region uses regional Cloud NAT with endpoint-independent redundant gateways distributed across separate failure domains, with multiple configured static NAT IPs. NAT capacity is sized from peak concurrent connections and egress, including failover headroom. Utilisation, port/IP exhaustion, errors, gateway loss, and loss of configured NAT capacity have defined thresholds and alerts. Gateway-loss and exhaustion tests are required. Separate NAT gateways are not conditional on subnet partitioning; any additional gateways required by subnet partitioning retain the same documented failure-domain and capacity rationale.
- Use the Regular release channel (Stable or Extended only if its support and feature requirements are explicitly justified), with a tested upgrade policy and maintenance window.

## 3. Application capacity

- Begin with at least 10 API replicas, distributed across zones. Six replicas at 800 requests/second provide only 4,800 requests/second and are invalid for this target; the 800 figure is only a benchmark assumption and must be remeasured under representative traffic.
- Requests, limits, node counts, and load-test results must demonstrate 5,000 requests/second with headroom during one-zone loss and node replacement or upgrade. Autoscaling must have sufficient quota and warm-up margin.

## 4. Placement and disruption

- Stateless tiers use topology spread constraints across zones and required hostname anti-affinity where one replica per node is required. Scheduling failures are visible and tested.
- A PDB permits controlled maintenance while preserving the tested availability objective (initially `minAvailable: 8` for 10 replicas, subject to load and zone-loss testing). It must not be set to 10/10.
- Node pools use surge upgrades with documented surge and unavailable values. Upgrade, drain, autoscaler, and one-zone-loss tests prove that capacity and PDB settings work together.

## 5. Traffic and regional recovery

- Use the global external Application Load Balancer with health-checked backends in both regions and health-based regional failover. Do not rely on a 3,600-second DNS change for a 15-minute RTO. Any DNS used by clients has a low, tested TTL and documented resolver and cache limitations.
- Health signaling has separate liveness, serving-readiness, and designated-writer/fencing-readiness conditions. The load balancer consumes writer-aware serving readiness. A fenced, read-only, stale, or non-current-writer region must fail write-serving readiness even if its pods are running. Promotion transitions, stale-client retries, and stale-client write rejection are tested.
- Regional recovery is a single-writer procedure: quiesce or fence writes in the old region, verify cross-region replica lag is within the promotion gate, promote the replica, update application database endpoints and secrets, validate the new writer, and only then advertise designated-writer readiness and enable the recovery backend. Client reconnection, old-region isolation, and rollback are documented. Load-balancer health alone does not provide write fencing.
- The recovery rehearsal measures complete RTO, including database promotion, application configuration, traffic shift, and validation.

## 6. Cloud SQL

- Cloud SQL for PostgreSQL HA is enabled in europe-west2, with automatic intra-region failover. Its HA standby is not used as a reporting endpoint.
- Dashboards use a separately provisioned supported read replica, with specified size, workload limits, freshness and lag monitoring, and behavior when unavailable or stale.
- Automated backups and point-in-time recovery are enabled. The cross-region asynchronous read replica is monitored continuously. Five-minute RPO is an objective with an explicitly accepted bound, not a replication guarantee: if lag exceeds the promotion gate, alert and follow the documented degraded or failover procedure, recording possible data loss.
- Promotion, write fencing, application endpoint changes, and client retries are rehearsed. Backup restore RTO is measured for the actual database size and workload, with a tested target and RPO. Restore is distinct from replica-promotion recovery.

## 7. CDC to BigQuery

- Datastream PostgreSQL logical-decoding prerequisites, permissions, version support, replication slot, WAL retention, quotas, and source-load impact are validated before production.
- End-to-end freshness is measured from source commit to queryable BigQuery data: target about five minutes, alert at three minutes, with a documented response to sustained lag.
- Slot/WAL growth, storage, source CPU/IO, and sink backpressure have hard alerts and bounded remediation. A stalled BigQuery destination must not exhaust storage or endanger the primary.
- CDC processing handles inserts, updates, deletes, ordering, retries, and replay according to a documented schema and idempotency design. A primary-key merge alone does not prove correct update history or delete handling. Recovery from Datastream restart and duplicate events is tested.

## 8. Security

- Workloads use Workload Identity for GKE, one least-privilege Google service account per tier, and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only approved pipeline-built images.
- BigQuery personal-data columns use policy tags, and datasets use customer-managed encryption keys.

## 9. Observability and operations

- SLIs are load-balancer request success rate and latency, with one-hour and six-hour error-budget burn alerts. Dependency incidents and client-visible regional failover count against the SLI and error budget. Planned maintenance is excluded only where the SLO contract explicitly permits it.
- Dashboards and alerts cover per-zone and node capacity, scheduling failures, autoscaler state, pod-range utilisation/exhaustion, NAT capacity, gateway errors and failures, load-balancer backend and writer-aware health, Cloud SQL health and connections, read-replica and cross-region lag, promotion readiness, Datastream freshness, slot/WAL retention, BigQuery sink failures, and recovery/fencing state.
- Runbooks define alert ownership, escalation, write freeze, promotion, client reconnection, and rollback.

## 10. Acceptance tests

Before production, run representative load and failover tests; one-zone loss; node drain and upgrade; autoscaler, quota, pod-range exhaustion, and surge-scheduling tests; NAT gateway-loss, capacity, exhaustion, and failure tests; read-replica failure; writer-aware health transitions and stale-client write rejection; Datastream restart, lag/backpressure, duplicate/update/delete replay; backup restore at representative database sizes; and regional promotion with write fencing.

Conduct a zone-failure game day at least quarterly and a full regional recovery rehearsal at least annually, each with measured SLO, RTO, and RPO results, defects, owners, and retest dates.