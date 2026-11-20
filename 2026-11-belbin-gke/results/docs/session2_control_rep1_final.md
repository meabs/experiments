# Highly Available GKE Platform Design

## 1. Goals and assumptions

This platform runs a customer-facing stateless web/API application at up to 5,000 requests/second for users in one continent. The target is 99.95% monthly availability (about 22 minutes of unavailability per 30-day month). It must tolerate loss of one availability zone without operator intervention. Loss of the primary region requires a documented, rehearsed recovery.

The primary deployment is a three-zone regional GKE Standard cluster. A second region contains a warm recovery environment. The application is stateless; the relational database and queue are managed services outside Kubernetes. The eight-person platform team favors managed services over operating distributed stateful systems.

Targets for regional disaster recovery are RTO ≤60 minutes and RPO ≤5 minutes. These targets must be validated by exercises and may be tightened only after measuring cost and application behavior.

## 2. Cluster and node topology

Create a private, regional GKE Standard cluster across three zones in the primary region, with private nodes and VPC-native alias IPs. Use separate regional node pools:

* A small system pool for DNS, metrics, ingress components, and other platform DaemonSets.
* A stateless application pool, autoscaled across all three zones.
* An optional batch/data-adjacent pool with taints and tolerations, so jobs cannot consume capacity reserved for serving traffic.

Use regional managed instance groups, surge upgrades, autoscaling, and sufficient reserved headroom that the remaining two zones can serve the required load after one-zone loss. Set resource requests realistically; enforce namespace quotas and limit ranges. Use multiple replicas (normally at least three) for every serving tier.

The secondary region has an independently provisioned, version-controlled GKE cluster and networking. It is warm rather than active-active: platform components and images are ready, while application capacity may be scaled down until failover.

## 3. Workload placement and disruption handling

Apply `topologySpreadConstraints` over zones and nodes, required pod anti-affinity for critical replicas, and zone-aware service routing. Do not permit all replicas of a tier to schedule in one zone. Define priority classes so critical serving pods preempt noncritical batch work if necessary.

Use HPAs driven by CPU plus request-rate/latency metrics where available, and Cluster Autoscaler with minimum capacity in every zone. Configure startup, readiness, liveness, and termination behavior so unhealthy pods leave endpoints before termination and connections drain.

Use PDBs that allow normal voluntary maintenance while preserving service: for example, at most one unavailable replica for a three-or-more-replica stateless tier, subject to testing. PDBs must not be used to block emergency recovery indefinitely. Ensure deployments use rolling updates with bounded surge/unavailable values, and use canary or progressive rollout for high-risk changes.

A zone failure is handled by GKE and the load balancer removing unhealthy endpoints, while pods are recreated in surviving zones. Capacity reservations/headroom and autoscaling prevent this from depending on manual intervention.

## 4. Traffic entry

Use a global external HTTPS Application Load Balancer with Google-managed certificates, regional GKE NEGs, health checks, Cloud Armor WAF/DDoS controls, and rate limiting. The primary region is the normal backend. A warm secondary-region backend is configured for disaster failover, with health checks that test meaningful application readiness rather than merely TCP reachability.

Prefer global load-balancer backend failover where it meets the application’s semantics; retain DNS failover as a documented fallback and keep DNS TTLs appropriate for the RTO. Health checks alone must not promote a database or change application write configuration. Regional failover is an explicit runbook operation, followed by validation and traffic shift.

Use internal load balancing/private connectivity for managed services. Do not expose databases, queue endpoints, or Kubernetes control-plane interfaces publicly.

## 5. Database and queue

Use regional HA Cloud SQL (or an equivalent managed relational service) with synchronous zonal standby, automated backups, point-in-time recovery, encryption, maintenance controls, and connection pooling. Provision a cross-region read replica or equivalent cross-region recovery mechanism. Replication is asynchronous unless an alternative is explicitly shown to meet latency and consistency requirements.

The application must tolerate transient database failover: bounded retries with exponential backoff, connection recycling, idempotent writes, and appropriate transaction timeouts. Monitor replication lag, storage, connections, locks, and failover status.

Use Pub/Sub or another managed regional HA queue rather than self-hosting brokers in Kubernetes. Configure retention, dead-letter topics/queues, acknowledgment deadlines, ordering and deduplication behavior as required by the application. Consumers must be idempotent. If strict broker semantics require self-hosting, provide an operator-supported topology, quorum policy, persistent disks, anti-affinity, backup, and a tested promotion procedure; this is a higher operational risk.

For regional recovery, promote the cross-region database replica (or restore to the recovery region), validate consistency and schema version, update secrets/configuration, and redirect queue producers and consumers. Record the expected data-loss window and any replay or reconciliation process. Kubernetes replicas are not a database backup or replication strategy.

## 6. Failure behavior and DR

For a zone failure, the load balancer stops sending traffic to failed endpoints; GKE reschedules pods, and autoscaling restores capacity in surviving zones. Alerting is generated, but no operator action is required for continued service. Validate that database HA and queue availability also survive a zone loss.

For a regional loss, declare disaster recovery, freeze nonessential changes, verify the incident and last replicated database position, promote or restore the database, activate/scale the secondary GKE workloads, configure the secondary region’s secrets and external dependencies, and switch global load-balancer/DNS traffic. Run smoke tests, verify queue consumers and data integrity, then communicate status. After restoration, reconcile writes and reverse replication/traffic only through a controlled plan.

Maintain a versioned DR runbook with owners, access prerequisites, decision points, rollback steps, customer communications, and commands. Exercise it at least twice yearly, including a timed RTO/RPO measurement.

## 7. Networking

Use separate subnets/ranges for nodes, pods, and services with IP capacity for autoscaling and future growth. Use VPC firewall rules with least privilege, private Google access, Cloud NAT for controlled egress, and Private Service Connect or private IP for managed services where supported.

Apply Kubernetes NetworkPolicies: default deny between namespaces, explicitly allowing ingress, DNS, metrics, database, and queue paths. Use Workload Identity Federation for GKE and short-lived service credentials; do not distribute static cloud keys in pods.

## 8. Upgrades and maintenance

Pin and regularly update supported GKE, node image, and add-on versions. Use release channels appropriate for production, test upgrades in a representative environment, and use surge upgrades one pool at a time. Preserve multi-zone capacity and respect PDBs while draining nodes. Schedule disruptive maintenance outside peak periods, but do not rely on maintenance windows for zonal resilience.

Use infrastructure-as-code, Git review, policy checks, artifact scanning, signed/approved images, and progressive application deployment. Keep rollback artifacts and database migration compatibility (expand/contract migrations) so old and new versions can coexist.

## 9. Observability and SLOs

Define SLIs for successful requests, latency, availability by endpoint, saturation, and dependency failures. The primary SLO is 99.95% monthly successful service availability; define latency objectives separately. Track an error budget and use it to control risky releases.

Collect centralized logs, metrics, traces, audit logs, load-balancer logs, Cloud SQL/queue metrics, and Kubernetes events. Alert on user-visible SLO burn rate, zonal endpoint loss, insufficient ready replicas, pending pods, autoscaler limits, node pressure, database failover/replication lag, queue age/backlog, certificate expiry, and backup/PITR failures. Dashboards must show capacity after loss of one zone.

## 10. Security affecting availability

Use least-privilege IAM, separate production identities, protected CI/CD, MFA, audit logging, secret management with rotation, and organization policies. Cloud Armor rules must be tested in preview before enforcement. Rate limits and quotas protect against abuse but have an explicitly monitored failure mode.

Backups are encrypted and access-controlled; periodically test restoration, not merely backup completion. Maintain break-glass access with logging and review. Security patches are prioritized without bypassing upgrade and rollback controls.

## 11. Validation, risks, and trade-offs

Before production, load test at and above 5,000 requests/second, test pod/node loss, cordon and evacuate each zone, exhaust a node pool, perform database failover, test queue backlog and duplicate delivery, execute faulty deployment rollback, restore backups, and run the full regional DR exercise.

Accepted trade-offs include the cost of three-zone headroom and a warm second region, asynchronous cross-region database replication and its bounded RPO, and managed-service feature/vendor dependence. A single-region zone failure is automatic, but regional recovery is not fully automatic because database promotion and data-integrity decisions require controlled human action. The design assumes the application is horizontally scalable, supports idempotency and retries, and can operate with the stated database/queue failover semantics.