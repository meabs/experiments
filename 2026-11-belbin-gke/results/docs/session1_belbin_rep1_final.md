# Highly Available GKE Platform Design

## Objectives and assumptions
- Customer-facing stateless web/API service, relational database, and message queue; peak 5,000 requests/s, one continent.
- Target service availability: 99.95% monthly (about 22 minutes downtime/month). The platform must tolerate loss of one zone without operator action. Regional loss has a documented, rehearsed DR procedure; it is not assumed to be transparent.
- Eight-person platform team and managed-service preference. Use regional managed GKE, Cloud Load Balancing, Cloud SQL HA/DR (or AlloyDB if database performance/feature requirements justify it), and a managed queue (Pub/Sub where semantics permit).
- Define RTO/RPO with product owners before production. Initial targets: zonal failure RTO 0 for stateless traffic and RPO 0 for committed database transactions; regional failure RTO 60 minutes and RPO <=5 minutes (tighten only if business-funded).

## Regional cluster and topology
- One regional, private GKE Standard cluster in three zones in the primary region, with control plane replicated by GKE. Use separate node pools for system, API/web, and batch/worker workloads.
- At least three zones, and minimum three replicas for every critical stateless Deployment. Spread replicas using `topologySpreadConstraints` across zones and nodes, required during scheduling where feasible; anti-affinity prevents same-node concentration.
- Regional subnets with secondary ranges for Pods and Services, VPC-native alias IPs, Private Google Access, Cloud NAT per zone/region as appropriate, and firewall rules default-deny.
- Autoscaling: HPA on CPU plus request rate/latency or queue depth; Cluster Autoscaler with headroom (for example, 20%) and separately sized pools. Set resource requests/limits from load tests; avoid overcommit for critical pods.
- Reserve capacity for zone loss: normal operation must leave enough aggregate capacity for all critical replicas after removal of the largest zone. Use priority classes and quotas so batch jobs cannot consume that reserve.

## Workload placement and disruption
- PodDisruptionBudgets allow at least two API replicas available (or 67% for larger fleets); do not use zero-disruption budgets that block upgrades forever. Workers use graceful drain and idempotent processing.
- Readiness gates, startup probes, liveness probes, termination grace periods, and preStop connection draining. Rollouts use `maxUnavailable: 0` and bounded `maxSurge`, with automatic rollback on error/latency SLO regression.
- Use separate namespaces, NetworkPolicies, service accounts, and resource quotas for platform, application, and jobs. Prefer managed ingress and queueing over exposing pods.
- Any single replica or zonally pinned workload is explicitly non-HA and has an owner/runbook.

## Traffic entry
- Global external HTTPS Application Load Balancer with a reserved anycast IP, managed certificates, Cloud Armor (WAF, rate limits, DDoS controls), and health checks. Backend is GKE Gateway/Ingress using NEGs; only ready endpoints receive traffic.
- Cloud DNS health-based failover points to the DR region when its independent health checks pass. Keep DNS TTL low enough for the RTO, but document resolver caching limits. Do not fail over solely because Kubernetes is unhealthy; require application and dependency health.
- Backend timeouts, retries, and circuit breaking are bounded. Retry only safe/idempotent requests, with request IDs and idempotency keys to prevent duplicate writes.

## Data tier
- Relational database runs outside the cluster as a regional HA managed instance with synchronous zonal standby, automated backups, point-in-time recovery, encryption with CMEK, and tested connection pooling. Multi-zone HA is not a substitute for backups.
- Cross-region replica/backup is continuously monitored. During regional DR, promote the replica (accepting stated RPO), fence the old primary, update a secret/config endpoint, and verify application migrations before allowing writes. Never permit split brain.
- Schema changes are backward-compatible expand/migrate/contract; migrations are serialized and reversible. Database connection exhaustion is alerted and load-shed before cascading failure.
- Use managed Pub/Sub (multi-zone durable service) unless strict ordering/transactional semantics require another managed queue. Configure retention, dead-letter topics, delivery attempts, idempotent consumers, bounded concurrency, and backlog alerts. Replicate/export critical messages for regional DR and document replay policy.
- Object storage holds immutable/versioned backups, manifests, and DR artifacts with retention/least privilege.

## Zone and region failure
- Zone loss: load balancer removes unhealthy endpoints; scheduler reschedules pods into surviving zones; autoscaler adds capacity. Database HA promotes within the managed service. Queue remains available. Alert and verify capacity, error rate, and replication; no manual traffic action expected.
- Region loss: declare incident, freeze writes if possible, fence primary, promote cross-region database, enable/verify DR cluster capacity and secrets, switch global routing, replay or reconcile queue data, run smoke tests, then announce service restoration. Fail back only after data reconciliation and a controlled change window.
- Maintain a versioned DR runbook with owners, prerequisites, commands, decision points, and customer communications. Keep the DR region warm enough to meet RTO (at least control plane, baseline nodes, images, and IaC); validate capacity quotas in advance.

## Upgrades and maintenance
- All infrastructure and Kubernetes objects are Terraform/GitOps managed; changes reviewed, staged, and audited. Pin supported GKE releases and use release channels with a tested soak period.
- Upgrade one node pool/zone at a time, respecting PDBs and spare capacity; canary application versions before broad rollout. Schedule maintenance in low-risk windows, with rollback criteria and an emergency pause.
- Regularly test cluster restore, node image rollback strategy, database PITR, and certificate rotation. Never depend on manual mutable cluster state.

## Networking and security
- Private nodes/control-plane endpoint where supported; restricted administrative access through identity-aware proxy/bastion, SSO, MFA, and just-in-time roles. No public SSH.
- Workload Identity, least-privilege IAM, Secret Manager with CSI integration and rotation, encryption in transit (TLS) and at rest, image signing/scanning, admission policy, and restricted host privileges.
- NetworkPolicies default deny; explicitly allow ingress, DNS, metrics, database, and queue paths. Central egress controls and NAT logging prevent accidental exfiltration.
- Protect quotas and dependencies from abuse with WAF/rate limits, per-tenant limits, bounded payloads, and backpressure. Security controls must have an emergency, audited break-glass path.

## Observability and SLOs
- Define SLIs at the load balancer and user journey: successful requests (availability), latency, and freshness/queue completion. Exclude explicitly documented client errors; do not hide server failures.
- Alert on burn rate (fast and slow windows), not every transient event. Initial objectives: 99.95% successful requests monthly; latency objective agreed from baseline (for example, 99% under 500 ms); queue age and DB replication lag bounded below RPO.
- Collect centralized structured logs, metrics, traces, audit logs, Kubernetes events, and database/queue telemetry with retention and cost controls. Dashboards show per-zone and dependency health. Alerts have runbooks, owners, and paging thresholds.
- Error budgets gate risky releases. Synthetic probes run from multiple locations, including DR endpoint; measure DNS and failover time.

## Validation, operations, and trade-offs
- Before production: multi-zone load/soak tests at peak plus headroom; kill pods/nodes, drain each zone, break dependencies, exhaust DB connections, backlog the queue, rotate certificates/secrets, and test autoscaler behavior.
- Quarterly game days simulate complete zone loss; at least twice yearly rehearse regional failover and restore, recording measured RTO/RPO and corrective actions. Test backup restores independently.
- Risks accepted: regional failover is not zero-downtime and may lose up to five minutes of committed asynchronous data; managed-service quotas, control-plane/provider outages, and DNS caching can exceed targets. Three-zone regional cost and warm DR cost more than single-zone/cold standby. Synchronous cross-region writes are rejected initially for latency/cost; reassess if RPO=0 becomes mandatory.
- Capacity, SLO, RTO/RPO, and DR assumptions are reviewed after traffic growth, dependency changes, or incidents.

DOC: content was posted in the shared room.