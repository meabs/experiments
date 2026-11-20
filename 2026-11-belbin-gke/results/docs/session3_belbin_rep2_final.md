# Highly Available GKE Platform Design

## 1. Goals and assumptions
- Customer-facing stateless web/API tier, relational database, and message queue; peak 5,000 requests/s.
- Target service availability: 99.95% monthly (about 22 minutes allowable unavailability), with automatic survival of any single-zone loss.
- A regional outage requires documented, rehearsed recovery rather than automatic multi-region active/active.
- Eight-person platform team and managed-service budget favor regional managed services over self-operated infrastructure.
- Application supports horizontal scaling, graceful shutdown, idempotent retries, and externalized session/state. Capacity tests establish actual CPU, memory, connection, and storage requirements.

## 2. Regional cluster and node topology
Deploy one regional private GKE Standard cluster across three zones in the primary region, with a regional control plane and separate node pools:
- system pool: three or more nodes, spread across zones;
- general workload pool: autoscaled and balanced across zones;
- optional compute-optimized pool for API/web workloads and memory-optimized pool for consumers.

Use minimum three nodes per pool where practical, multiple machine types only when justified, shielded nodes, and Container-Optimized OS. Use zonal topology spread constraints and `podAntiAffinity` so replicas do not co-locate. Do not run the relational database on Kubernetes.

Size each zone so the two surviving zones can serve the full 5,000 requests/s peak after loss of any one zone, with tested reserve (for example, 30% CPU/memory headroom). Verify regional quotas, node-pool limits, and Cluster Autoscaler surge capacity for this scenario.

Use separate namespaces and service accounts for web/API, workers, platform components, and observability. Apply ResourceQuota, LimitRange, Pod Security Admission (restricted), and NetworkPolicy defaults.

## 3. Workload placement and disruption
Run at least three replicas of each critical stateless deployment, distributed across all zones. Set realistic requests/limits, readiness/startup/liveness probes, rolling updates (`maxUnavailable: 0`, bounded `maxSurge`), and a PodDisruptionBudget that leaves at least two replicas available (or an equivalent percentage for larger fleets). Use graceful termination and connection draining.

Readiness checks must be dependency-aware: do not route traffic to instances that cannot reach required database, queue, or other essential services. Liveness checks must not turn transient dependency failures into restart storms.

Use Horizontal Pod Autoscaler on CPU/memory plus application metrics (request rate/latency); use node autoscaling with sufficient headroom. Configure cluster autoscaler to balance zones and use priority classes so critical workloads preempt noncritical batch jobs only if necessary. Queue consumers scale from queue depth while respecting downstream database limits. Dead-letter queues and idempotency prevent retry storms.

## 4. Traffic entry
Use a global external HTTPS Application Load Balancer with a regional GKE Gateway/Ingress, managed TLS certificates, HTTP(S) health checks, Cloud Armor WAF/rate limiting, and CDN caching for suitable static content. Reserve static addresses and use DNS with low TTL for disaster recovery. The load balancer sends traffic only to ready endpoints; enable connection draining and timeouts. Preserve client identity through trusted proxy headers and log it safely.

For regional disaster recovery, maintain a warm, scaled-down GKE cluster in a second region (or a documented rebuild path if cost constraints prohibit warm capacity), replicated configuration and images, and a tested DNS/load-balancer failover procedure. The secondary backend must be gated on successful database promotion and application/data-readiness validation, not infrastructure health alone.

## 5. Stateful data tier
Use regional/high-availability managed PostgreSQL (for example Cloud SQL HA) with automated backups, point-in-time recovery, encryption, maintenance controls, and a cross-region read replica or backup copy. Choose storage, connection limits, and transaction sizing from load tests. Put PgBouncer or a managed connection pooler in front where appropriate; monitor pool saturation.

Use a managed regional message queue (for example Pub/Sub) with multi-zone durability, acknowledgment deadlines, retry policy, dead-letter topics, ordering only where required, and retention sized for regional recovery. If Kafka semantics are mandatory, use a managed multi-zone service instead of a single in-cluster broker.

The database is the principal regional recovery dependency: document RPO (target <=5 minutes using continuous replication/backups) and RTO (target <=60 minutes, confirmed by rehearsal). During failover, fence or stop the primary to avoid split brain, promote the replica/restore, rotate application connection configuration, and validate migrations and consistency. Accept possible loss of unreplicated transactions and explicitly communicate it.

## 6. Failure behavior
**Single zone:** the regional control plane and surviving node pools continue; topology rules reschedule pods into surviving zones, autoscaling adds capacity, and the load balancer removes unhealthy endpoints. The surviving zones are pre-sized and tested to handle 5,000 requests/s with reserve. Managed database and queue remain available through their regional HA design.

**Regional outage:** declare disaster, stop or fence the primary to avoid split brain, promote the secondary database, deploy/scale workloads in the DR region, validate queue handling and secrets/configuration, and perform application/data-readiness checks. Only then shift global load-balancer/DNS traffic. Run a reconciliation procedure for writes and queued messages. Record RTO/RPO results and customer impact.

Planned maintenance, failover time, dependency outages, database promotion, and DNS/load-balancer convergence all consume the 99.95% availability error budget; they are not excluded from the availability SLO.

## 7. Upgrades and maintenance
Use release channels with a tested canary node pool and workload canary. Upgrade one zone/node pool at a time, respecting PDBs and capacity; never drain all replicas of a service simultaneously. Test Kubernetes, node image, ingress, and application changes in a staging cluster. Pin and scan images, use signed artifacts and rollback-capable manifests. Schedule disruptive maintenance outside peak hours but design for no-downtime operation. Database schema changes use backward-compatible expand/migrate/contract steps.

## 8. Networking
Use VPC-native GKE, private nodes, private Google access, Cloud NAT with redundant regional capacity, and restricted control-plane authorized networks/private endpoint. Segment subnets and firewall rules by environment; deny unnecessary east-west traffic with NetworkPolicy. Use Private Service Connect/private IP for managed database and services where supported. Plan IP ranges for maximum pods/services and future clusters. Set egress controls and monitor NAT port exhaustion.

## 9. Observability and SLOs
Collect metrics, logs, traces, audit logs, Kubernetes events, load-balancer logs, database metrics, queue age/depth, and deployment markers in a centralized system with retention and access controls. Alert on user-facing symptoms:
- availability SLO: 99.95% successful valid requests;
- latency SLO: define endpoint-specific target (for example 99th percentile <=500 ms for reads) after load testing;
- queue age/consumer lag, database connections/replication lag, error rate, saturation, and zone imbalance.

Use burn-rate alerts (fast and slow), synthetic probes from multiple locations, and on-call escalation with runbooks. Exclude intentionally rejected/rate-limited traffic only if the SLO definition is explicit and auditable. Planned maintenance, DNS/LB convergence, database promotion, failover, and dependency outages remain part of the availability measurement and error budget.

## 10. Security affecting availability
Use least-privilege IAM, Workload Identity, separate production projects, MFA, short-lived credentials, Secret Manager with controlled rotation, and CMEK where required. Protect the control plane and CI/CD, require reviewed changes, vulnerability scanning, admission policy, and image provenance. Cloud Armor and quotas limit abuse; backups and recovery keys are tested. Avoid security controls that create a single dependency; monitor certificate, secret, quota, and key expiry. Maintain audited break-glass access and test it periodically.

## 11. Validation and operations
Before production, load-test at peak plus burst, including a zone-loss test proving the two surviving zones sustain 5,000 requests/s with the selected reserve. Verify quotas, autoscaler surge behavior, dependency-aware readiness, and database connection limits.

Run game days for pod/node loss, each-zone loss, database failover, queue backlog, bad deployment rollback, certificate/secret rotation, NAT exhaustion, and regional failover. Rehearse regional recovery at least quarterly and zone-failure scenarios monthly. Verify backup restoration, RPO/RTO, DNS/load-balancer behavior, data-readiness gates, and customer communications. Maintain diagrams, ownership, escalation paths, and runbooks.

## 12. Risks, assumptions, and trade-offs
- One primary region cannot provide availability during a regional outage; warm DR costs more but materially reduces RTO.
- Database failover and cross-region replication determine actual RPO/RTO; application writes must tolerate retries and possible duplication.
- Kubernetes HA does not make an unsuitable application HA; dependencies, quotas, connection pools, and capacity require testing.
- Three zones, spare capacity, managed HA database/queue, and global ingress increase cost, accepted to meet 99.95%.
- Automatic failover can amplify corruption or bad releases; require fencing, health validation, and controlled promotion.
- Exact replica counts, machine sizes, latency targets, and database topology are finalized from load and failure tests, not guessed.