# Highly Available GKE Platform Design

## Goals and assumptions
- One-continent customer service, peak 5,000 requests/s, target 99.95% monthly availability (about 22 minutes error budget), and no manual action for loss of one zone.
- Stateless web/API, relational database, and durable message queue. Define “available” as successful authenticated API/web requests and documented queue operations; measure separately for dependencies.
- Use two GCP regions in the continent (primary and warm standby), three zones per region where available. Regional recovery is documented and rehearsed, but is not claimed as automatic unless the application has been proven safe for it.
- Eight-person platform team favors managed services and boring, repeatable operations. Capacity and quotas are validated with load tests before launch.

## Cluster and node topology
- Run one **regional, private GKE Standard** cluster in the primary region, spread across three zones, with control plane managed by GKE. Create a separately managed regional standby cluster (not a stretched cluster) using the same Terraform and GitOps releases.
- Separate node pools: small system pool (three zones, autoscaling), general application pool, and optional workload-specific pool. Use regional managed instance groups, autoscaling, surge upgrades, and at least two nodes per zone at normal load. Reserve headroom of at least one zone’s application capacity plus 30%; test quota and IP capacity.
- Use namespaces, ResourceQuota, LimitRange, Pod Security admission, and Workload Identity Federation. Keep cluster add-ons minimal and managed. Pin supported GKE versions and release channels; never run production on an end-of-life version.

## Workload placement and disruption
- Deploy at least three replicas for each stateless service, with topology spread constraints across zones and pod anti-affinity. Set realistic CPU/memory requests, startup/readiness/liveness probes, graceful termination, and a PodDisruptionBudget (normally maxUnavailable 1).
- Horizontal Pod Autoscaler scales on CPU plus request rate/latency where available; Cluster Autoscaler expands pools. Queue consumers scale on backlog. Load tests establish min/max replicas and scale-up time.
- Use rolling Deployments with maxUnavailable 0 and controlled maxSurge, backward-compatible schema/API changes, canaries, and automatic rollback on SLO burn. Do not use PDBs to block a zone failure; they only protect voluntary disruption.

## Traffic entry and networking
- Global external HTTPS Application Load Balancer with Google-managed certificates, Cloud Armor (WAF/rate limits), health checks, and backend services targeting the primary regional GKE ingress/Gateway. Global DNS/anycast directs users to healthy capacity; standby is either warm and health-checked or explicitly promoted by the tested regional runbook.
- VPC-native private cluster, separate subnets and secondary ranges for Pods and Services, Private Google Access, Cloud NAT per region, and restricted firewall rules. Use private service access for managed dependencies. NetworkPolicy defaults deny and explicitly allow required flows.
- Use multi-zone regional load balancing, connection draining, request timeouts, retries only for idempotent operations, and bounded circuit breakers. Protect the database from retry storms.

## Stateful data tier
- Prefer Cloud SQL for PostgreSQL/compatible relational data, regional HA (synchronous standby in another zone), automated backups, point-in-time recovery, encryption, maintenance windows, and tested failover. Use connection pooling (for example PgBouncer) with strict pool limits.
- Replicate asynchronously to a Cloud SQL cross-region read replica or another supported managed regional standby. Promote only through a documented, idempotent runbook after fencing the old primary; accept a stated RPO (for example 5 minutes) for regional loss. Application writes must tolerate reconnects and duplicate-safe retries.
- Use a managed durable queue (for example Pub/Sub) with regional/cross-region design, retention, dead-letter topics, exponential retry, ordering only where required, and idempotent consumers. Do not treat “message accepted” as database commit unless an outbox/inbox pattern is implemented.
- Backups are encrypted, retention-locked where appropriate, stored independently/cross-region, and restore-tested quarterly. Secrets use Secret Manager and rotation.

## Failure behavior
- **Single zone:** regional GKE and managed database failover, topology spread, and load balancers remove unhealthy endpoints; autoscaling replaces capacity. Queue retains work. Alerts page only if SLO/error budget is threatened; no operator action is required.
- **Regional loss:** global health checks stop serving the primary; execute the promotion runbook to activate standby GKE, promote the database replica, update configuration/DNS/routing, validate migrations and queues, and communicate status. RTO target is documented and tested (initial target 60 minutes), RPO target 5 minutes subject to replication. Prevent split brain with fencing/lease and a single-writer switch.
- DR runbook includes dependencies (DNS, certificates, IAM, quotas, images, secrets, third-party endpoints), rollback, and customer communication. Rehearse at least twice yearly.

## Upgrades and maintenance
- Terraform manages projects, VPC, IAM, clusters, node pools, load balancing, and databases; GitOps manages Kubernetes manifests. All changes reviewed, automated-tested, and auditable.
- Upgrade standby first, then canary workloads and primary node pools using surge upgrades; maintain capacity and PDBs. Test application compatibility before control-plane/node upgrades. Schedule disruptive database maintenance inside an error-budget-approved window.
- Keep two prior application versions deployable; use expand/contract migrations and backups before destructive changes. Define emergency change and rollback procedures.

## Observability and SLOs
- Centralize logs, metrics, traces, audit logs, and GKE control-plane logs with retention and access controls. Dashboards show global/region/zone request rate, availability, latency percentiles, saturation, pod restarts, pending pods, node health, load-balancer health, database replication lag/connections/locks, queue age/backlog, and backup/failover status.
- SLOs: 99.95% monthly successful requests; latency objective agreed per endpoint (for example 99th percentile <500 ms); queue processing age objective; database backup/replication objectives. Burn-rate alerts page for fast and slow breaches; capacity, certificate, quota, replication-lag, and backup alerts are actionable and routed to on-call.
- Maintain a service catalog, ownership, runbooks, escalation and incident timeline. Error budget gates risky releases.

## Security that protects availability
- Organization policies, least-privilege IAM, separate deploy/runtime identities, MFA, private control plane access, approved admin access paths, binary/image vulnerability scanning and signing, admission policy, and immutable artifact registry.
- Encrypt in transit and at rest; rotate secrets/certificates; WAF/DDoS controls and quotas prevent abuse. Ensure security controls have HA (multiple NAT/relay paths where needed) and emergency break-glass access is tested and audited.

## Validation, risks, and trade-offs
- Before launch perform load/soak tests at peak plus headroom, zone evacuation, node/pod disruption, database failover, queue redelivery, certificate/secret rotation, dependency outage, restore, and regional DR exercises. Record measured RTO/RPO and remediate findings.
- Risks: cross-region database replication can lose recent writes; managed-service quotas/maintenance and cloud-wide outages remain possible; global LB health checks can lag; stateful failover can cause duplicate work. Mitigate with explicit RPO, fencing, idempotency, backups, quota reservations, and rehearsals.
- Two clusters and cross-region replicas cost more and add operational complexity, while a single region cannot meet regional DR requirements. Automatic zone recovery is prioritized; regional recovery remains controlled to avoid split brain and corruption.
- Launch gates: demonstrated 5,000 requests/s with headroom, zone loss without SLO violation, successful restore and DR rehearsal, monitored alerts/runbooks, and agreed SLO/RTO/RPO sign-off.


PASS