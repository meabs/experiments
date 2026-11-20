# Highly Available GKE Platform Design

## 1. Scope, targets, and assumptions

This platform runs a stateless customer-facing API/web tier and a message queue for users in one continent. Peak load is approximately 5,000 requests/second. The service target is 99.95% monthly availability. It must tolerate loss of one zone without operator intervention. Regional loss requires documented and rehearsed disaster recovery.

The platform is managed by eight engineers, so managed Google Cloud services are preferred over self-operated infrastructure. Initial design assumptions are: one active production region, three zones, a single-writer transactional database, and an RPO of at most 15 minutes and RTO of at most 60 minutes for regional disaster recovery. The database and application must be sized and load-tested; autoscaling is not a substitute for capacity planning.

## 2. Regional and cluster topology

Use a regional GKE Standard cluster in three zones, with private nodes and the control plane managed by Google. Use separate node pools for:

* system and ingress components;
* general API/web workloads;
* queue consumers and other latency-sensitive workers;
* optional memory/CPU-optimized pools for exceptional workloads.

Use Compute Engine machine types sized from load tests, with spare capacity in every zone. Enable cluster autoscaling with per-pool minimums in all zones and a capacity buffer. Use zonal Persistent Disks only for workloads that genuinely require them; prefer managed external state. Do not run PostgreSQL or the durable queue as ordinary cluster workloads.

Use separate namespaces and Google Cloud projects/service accounts for production, staging, and platform components. Pin supported GKE versions, use release channels, and maintain an upgrade runbook.

Workloads must specify requests and limits, startup/readiness/liveness probes, a PodDisruptionBudget, and at least three replicas for critical stateless services. Use topology spread constraints and anti-affinity across zones and nodes. Critical deployments use rolling updates with `maxUnavailable: 0` where capacity permits. Queue consumers must be idempotent and support graceful termination. A failed zone is handled by rescheduling into the two remaining zones; admission capacity and autoscaler limits must already support this.

Use a managed durable queue (for example Pub/Sub) rather than relying on in-cluster broker disks. Configure retention, dead-letter topics, retry/backoff, ordering keys only where required, and bounded subscriber concurrency.

## 3. Traffic entry and networking

Expose the application through a global external HTTPS Load Balancer using a regional GKE Gateway/Ingress, managed certificates, HTTP-to-HTTPS redirect, Cloud Armor, and rate limiting/WAF rules. Health checks must test application readiness without depending on a noncritical downstream. Use CDN caching only for explicitly public immutable content; never cache personalized responses.

Nodes use private IPs. Use a dedicated VPC, regional subnets with planned secondary ranges for Pods and Services, Cloud NAT for controlled egress, Private Google Access, and Private Service Connect/private IP connectivity to Cloud SQL. Firewall rules are least-privilege and deny by default. Egress is restricted through approved NAT/proxy paths where practical. DNS, certificate, quota, and IP-range ownership are documented.

## 4. Transactional database

Use Cloud SQL for PostgreSQL with regional high availability (primary and synchronous standby in separate zones), automatic failover, point-in-time recovery, automated backups, and deletion protection. Select a supported version and a machine/storage configuration with headroom for peak traffic, maintenance, replication, and CDC. Enable regional storage where supported and monitor storage growth, IOPS, connections, locks, and replication health.

Applications connect through the Cloud SQL connector or Auth Proxy with private IP and IAM/database authentication, using connection pooling (for example PgBouncer where appropriate). Configure bounded pools so failover cannot create a connection storm. Retry only safe, transient connection failures with exponential backoff and jitter; transactions must be idempotent or use request IDs. Do not automatically retry an unknown-commit transaction without an idempotency key.

Cloud SQL HA handles a zonal failure. During failover, existing connections fail and writes pause briefly; clients reconnect to the writer endpoint. Test failover at load. Backups and WAL/PITR are retained according to compliance requirements and copied/replicated to a separate recovery region. Read replicas may serve explicitly noncritical reads but are not a substitute for HA.

## 5. Change data capture and BigQuery

Use Datastream for PostgreSQL CDC, writing into a regional or dual-region Cloud Storage landing area, followed by Dataflow (or an equivalent managed ingestion job) into BigQuery raw and curated tables. CDC reads from PostgreSQL logical replication/WAL, not polling application tables. Provision and monitor replication slots and WAL retention so a stalled pipeline cannot fill database storage. CDC settings, slot limits, and added source overhead are load-tested; alerts fire well before WAL exhaustion.

The CDC stream includes operation type, source commit timestamp, transaction/LSN (or equivalent source position), table/schema, and a stable event identifier. BigQuery raw tables are append-only and retain the original event. A deduplication/merge job uses the event identifier/source position and primary key plus ordering metadata to produce curated current-state and history tables. Consumers must expect at-least-once delivery, duplicates, retries, and eventual rather than globally ordered arrival. Events are ordered per source transaction/table where supported; no cross-table total order is promised unless explicitly implemented.

Initial load is performed with Datastream backfill or a consistent snapshot, records its snapshot watermark, then applies changes after that watermark. Reconcile row counts, checksums, and maximum source positions before declaring the table current. Run the initial load off-peak and monitor source CPU, I/O, locks, WAL, and application latency.

Schema changes use an expand-and-contract process: add nullable/new fields first, deploy compatible consumers, backfill, then remove/rename only after retention and consumer sign-off. CDC schema drift is quarantined and alerted rather than silently discarding data. Changes to keys, types, or tables require a migration review.

CDC is configured against the Cloud SQL writer and must reconnect after a managed database failover, preserving its replication position. Validate this in tests and alert on slot lag. If the primary region is lost, CDC is stopped or redirected to the promoted recovery database only after the recovery point is established; the documented result is a possible gap/duplicate bounded by the DR RPO, followed by replay/reconciliation from WAL/backup and raw landing data. BigQuery datasets and landing storage are multi-region or replicated to the recovery region.

Personal data is minimized: replicate only approved columns/tables, tokenize or hash identifiers where analytics permits, encrypt in transit and at rest, restrict BigQuery row/column access with IAM and policy tags, and apply masking, retention, deletion propagation, audit logging, and legal hold procedures. CDC raw data has the same or stricter access controls as the source. A deletion request must remove or tombstone the person in curated and raw datasets according to policy.

Freshness SLO: at least 99% of committed changes are queryable in curated BigQuery within five minutes, measured from source commit time, with separate alerts for source lag, transport lag, and transformation lag.

## 6. Availability and regional disaster recovery

For a zonal failure, the load balancer removes unhealthy endpoints, GKE reschedules pods, the autoscaler adds capacity in surviving zones, Cloud SQL performs HA failover, and Pub/Sub retains unprocessed messages. Operators verify capacity and error rates but no manual action is required for service restoration.

For regional loss, maintain infrastructure-as-code, container images, configuration, secrets, and approved database backups/exports in a separate recovery region/project. Keep a warm or rapidly deployable GKE cluster and pre-created networking, quotas, IAM, DNS, certificates, and BigQuery recovery datasets. Promote/restore Cloud SQL using the latest valid backup/PITR position, update the writer secret/endpoint, deploy the application, and shift global load-balancer/DNS traffic after smoke tests. Freeze or clearly fence the old region to prevent split brain. Document customer communication and data-loss expectations.

Run a full regional recovery at least annually and partial exercises quarterly. Record measured RTO/RPO and update runbooks.

## 7. Upgrades, maintenance, and change control

Use Terraform (or equivalent) and Git-reviewed changes. Separate application, cluster, database, and networking changes. Use canary/rolling application releases, backward-compatible database migrations, and automated rollback. GKE upgrades are tested in staging, then performed in a maintenance window with surge capacity, PDB validation, and zone-by-zone disruption monitoring. Cloud SQL maintenance follows HA guidance and is scheduled with customer notice. CDC compatibility is a release gate.

## 8. Observability and SLOs

Collect centralized structured logs, metrics, traces, audit logs, and Kubernetes events with sensitive-data redaction. Dashboards and alerts cover:

* availability, latency (including p95/p99), error rate, saturation, and request rate;
* per-zone pod/node health, pending pods, evictions, capacity, and autoscaler actions;
* load-balancer health, TLS, WAF blocks, DNS, NAT, and quota exhaustion;
* Cloud SQL CPU, memory, storage, connections, locks, transaction latency, backups, failovers, WAL and CDC slot retention;
* queue age, backlog, delivery attempts, dead letters;
* CDC source/transport/transform lag, failed records, duplicates, schema drift, and BigQuery freshness.

Define the 99.95% availability SLO using successful customer requests, excluding only explicitly documented invalid requests; track an error budget and use it to govern risky changes. Page on customer-impacting symptoms, database imminent exhaustion, queue loss risk, and CDC freshness/WAL thresholds. Runbooks include escalation and rollback steps.

## 9. Security affecting availability

Use least-privilege IAM, separate deploy/runtime identities, Workload Identity, Secret Manager with controlled rotation, CMEK where required, vulnerability scanning, image signing/admission policy, and audited break-glass access. Keep at least two platform administrators and tested recovery access so IAM mistakes do not lock out operations. Back up Terraform state and critical secrets/configuration securely. Apply organization policies, private endpoints, audit retention, and regular access reviews.

## 10. Failure testing, risks, and trade-offs

Regularly test pod/node loss, each-zone evacuation, load-balancer/backend failure, Cloud SQL failover, connection storms, queue redelivery, CDC restart/duplicate delivery, schema changes, BigQuery outage, expired certificates/secrets, quota exhaustion, and regional recovery. Tests use production-like traffic and verify SLOs, data reconciliation, alerting, and runbook usability.

Accepted trade-offs are a single active region (lower cost but regional DR is slower), managed CDC/queue costs and at-least-once semantics (simpler operations but deduplication is required), and planned capacity headroom (costly but necessary for zonal survival). Risks include regional quota shortages, untested application retry behavior, WAL growth during CDC outage, schema incompatibility, and personal-data leakage; each has an owner, alert, mitigation, and review date.