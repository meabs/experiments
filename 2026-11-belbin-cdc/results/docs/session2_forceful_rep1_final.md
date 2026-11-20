# Highly Available GKE Platform Design

## 1. Goals and assumptions

This platform runs a customer-facing stateless web/API service and a message queue for one-continent traffic. Peak load is approximately 5,000 requests/second. The service target is 99.95% monthly availability (about 22 minutes of unavailability/month). It must tolerate loss of one zone without operator action. Regional loss requires documented, rehearsed recovery.

The database is Cloud SQL for PostgreSQL. Analytics requires committed database changes in BigQuery within five minutes, without materially increasing primary-database load or reducing availability. Tables contain personal data.

Assumptions: the application is horizontally scalable and can retry idempotently; queue messages have stable IDs and are safely redeliverable; one GCP region is the primary serving region; a secondary region is maintained for disaster recovery; RTO for regional disaster is four hours and RPO is the agreed Cloud SQL backup/replication point (target under one hour unless a stronger cross-region database design is funded). Google-managed control planes and regional services are dependencies.

## 2. GKE topology and workload placement

Use a **regional private GKE Standard cluster** in three zones in the primary region. Use VPC-native alias IPs, separate node and pod secondary ranges, and Workload Identity Federation for GKE. Enable release channels (Regular, with upgrades tested in a staging cluster first), control-plane authorized networks, Shielded nodes, and Dataplane V2/network policy.

Use separate node pools:
- General-purpose pool for API/web workloads, spread across all zones using topology spread constraints and pod anti-affinity.
- Queue-worker pool, independently autoscaled and tainted so web traffic cannot consume all capacity.
- System pool reserved for DNS, ingress, metrics, and other cluster services.
- Optional memory/CPU-optimized pool for explicitly approved workloads.

Set minimum capacity in every zone sufficient to run the critical service after losing one zone. Cluster autoscaler must scale across zones, and quotas/reservations must cover failover capacity. Use PodDisruptionBudgets (PDBs), readiness/startup probes, graceful termination, rolling deployments, and replicas at least three (more based on load testing). PDBs must not block emergency node replacement indefinitely. Do not use zonal persistent disks for a cross-zone-critical workload; prefer stateless pods and managed services.

The application uses Kubernetes Services and an external global HTTPS load balancer through GKE Gateway/Ingress. Managed certificates, HTTP health checks, Cloud Armor, rate limits, and backend timeouts are configured. The load balancer sends traffic only to ready endpoints and supports controlled draining.

The queue is a managed regional/multi-zone service where possible. Workers use at-least-once processing, acknowledgements only after durable handling, exponential backoff, dead-letter queues, and idempotency keys. Queue backlog is an availability and SLO signal.

## 3. Traffic, networking, and dependencies

DNS points to the global external HTTPS load balancer with low enough TTL for planned changes. TLS terminates at the load balancer with modern policies; service-to-service traffic uses authenticated, encrypted connections. Cloud Armor provides WAF, DDoS protection, and abusive-client controls.

Use separate projects for production, staging, security/logging, and analytics where practical. Apply Shared VPC, hierarchical firewall policies, least-privilege service accounts, private Google access, and Private Service Connect/private IP paths to managed services. No public node IPs. Egress is restricted through Cloud NAT and, where required, an egress proxy with logging. Use VPC Flow Logs, firewall logging, and organization policy constraints.

Reserve IP ranges and quotas in advance for nodes, pods, services, load balancers, Cloud SQL, NAT, and the DR region. Define dependency timeouts, circuit breakers, bounded retries with jitter, and overload protection; retries must not amplify an outage.

## 4. Transactional database

Use Cloud SQL for PostgreSQL with regional high availability (synchronous standby in a different zone), private IP, automated backups, point-in-time recovery, deletion protection, CMEK where required, and maintenance windows. Select a size based on load testing with at least 30% headroom for CPU, memory, connections, storage I/O, and WAL. Use connection pooling (for example, PgBouncer or an application-managed pool) to protect Cloud SQL from connection storms.

Use read replicas only for explicitly read-only traffic; never direct writes to them. The application connects using the Cloud SQL Auth Proxy/connectors or private authenticated connectivity and must transparently retry safe transactions after failover. Transactions are short, indexes and query plans are reviewed, and schema migrations are backward-compatible expand/contract changes.

Cloud SQL HA provides automatic zonal failover; expect a short interruption and ensure the application reconnects. Monitor replication/HA state, failover events, connections, locks, long transactions, WAL generation, storage, CPU, latency, and errors. Backups are encrypted and regularly restored into an isolated project.

For regional disaster, maintain a cross-region read replica or equivalent supported cross-region replication design if the required RPO justifies its cost. Promote only through a runbook with fencing/connection cutover to prevent split brain. If cross-region replication is not enabled, restore the newest verified backup/PITR into the DR region; state the resulting RPO explicitly. The DR database is not considered serving until integrity checks and application smoke tests pass.

## 5. Change data capture and BigQuery

Deploy a managed CDC service (for example, Datastream) reading PostgreSQL logical replication/WAL through a private path, writing to a regional Cloud Storage landing area, and loading BigQuery through Dataflow/BigQuery ingestion. Keep CDC credentials separate and grant replication/read access only to required schemas/tables. Configure a replication slot with monitored WAL retention limits; alert and stop/repair the pipeline before retained WAL threatens database storage.

CDC reads committed changes from WAL rather than polling tables, avoiding application query load and minimizing source impact. Size and load-test replication slots, WAL, CPU, I/O, and network overhead. If supported, use a logical-decoding user and publication limited to analytics tables; never replicate secrets unnecessarily.

The pipeline must preserve source transaction/order metadata (LSN, transaction ID, commit timestamp, table, operation, and primary key). BigQuery landing tables are append-only and partitioned by event/commit date. A deduplication/merge stage uses a deterministic event key such as source identity plus LSN/sequence, with transaction ordering retained within the limits documented by the CDC product. Delivery is at least once: duplicates are expected and removed by idempotent merges. Consumers must tolerate temporary lag and replay.

Define the freshness SLO as at least 99% of eligible committed changes queryable in curated BigQuery tables within five minutes, measured from source commit timestamp; alert at three minutes and page at five. Track capture lag, source WAL/slot retention, object arrival, processing lag, rejected records, duplicates, and BigQuery load errors.

On Cloud SQL failover, the CDC connector must reconnect to the promoted primary using a stable instance endpoint and resume from its checkpoint/LSN. Validate that the connector does not create competing slots or silently skip changes. Pause/resume and reconciliation procedures compare source row counts/checksums and CDC positions.

For regional recovery, stop/fence the old connector and database first. Start a separately documented DR connector against the promoted/restored database with a new source identity, record the cutover timestamp/LSN, and accept that changes after the last replicated backup/CDC point may be missing or replayed. Reconcile and deduplicate before declaring analytics current. During the transition, label BigQuery data as primary-region or DR-era and communicate the freshness/RPO gap.

Initial backfill runs from a consistent database snapshot or CDC-consistent snapshot into temporary/staging tables, in batches throttled to protect production. Capture WAL changes during the backfill, then apply the ordered delta and cut over atomically. Validate counts, checksums, nullability, and key ranges. Schema changes use an expand/backfill/contract process: add nullable columns/tables first, deploy compatible readers/writers, update CDC and BigQuery schemas, backfill, then remove old fields only after retention and consumer approval. Quarantine incompatible records rather than dropping them.

Personal data is minimized in replicated columns, classified and tagged in BigQuery, encrypted in transit/at rest, and protected with IAM, row/column-level security, policy tags, authorized views, and audit logs. Apply retention/deletion propagation procedures (including subject deletion requests), restrict exports, and use masked/tokenized values for analytics where possible. Never log payloads or credentials.

## 6. Availability, failure handling, and recovery

A zone loss causes load balancer endpoint removal, pod rescheduling, and queue-worker redistribution. Remaining zones have preplanned capacity. PDBs and topology constraints prevent voluntary disruption from removing too many replicas, while readiness gates prevent traffic before dependencies are usable.

A regional loss triggers the DR runbook: declare incident, stop/fence old writers and CDC, verify DNS/load-balancer and IAM/network prerequisites, promote cross-region database or restore backup, start DR GKE workloads, point traffic to DR, validate queue and database consistency, start the DR CDC connector, and communicate the known RPO/analytics gap. Replay or reconcile queued work, then monitor. Failback is a separately reviewed operation, never an automatic reverse promotion.

Use quarterly game days for zone failure, Cloud SQL failover, node-pool loss, queue backlog, CDC outage/WAL pressure, BigQuery outage, and regional DR. Perform at least annual full regional recovery with measured RTO/RPO. Restore backups monthly in an isolated environment and test CDC snapshot/backfill procedures.

## 7. Upgrades, maintenance, and changes

Use infrastructure as code, Git-reviewed changes, separate staging, canary deployments, progressive production rollout, and automated rollback. Test Kubernetes/GKE, database engine, connector, schema, and application upgrades against representative traffic and CDC data. Maintain a change calendar and avoid simultaneous database, cluster, and network maintenance.

Use surge upgrades and capacity headroom; preserve PDB requirements but provide an approved emergency override. Database maintenance is scheduled in the lowest-risk window and communicated. Pin and regularly update container images, base OS packages, and dependencies; scan images and sign/verify artifacts.

## 8. Observability and SLOs

Collect metrics, structured logs, traces, Kubernetes events, load-balancer logs, Cloud SQL logs, audit logs, queue metrics, CDC metrics, and BigQuery job/load metrics in a centralized, access-controlled system. Alert on user-impacting symptoms first.

Track service availability, request latency (including p95/p99), error rate, saturation, queue age/backlog, pod readiness/restarts, node capacity, Cloud SQL failover/latency/connections/storage/WAL, CDC freshness and slot retention, BigQuery load failures, and DR replication lag. Define an error budget for 99.95%; freeze risky changes when the budget is exhausted. Synthetic probes exercise the complete user path and a representative write/read transaction.

## 9. Security and operational ownership

Use least privilege, short-lived credentials, Workload Identity, Secret Manager with rotation, CMEK/key-availability monitoring, centralized audit logs, vulnerability management, and break-glass access with approval and recording. Document on-call ownership, escalation, runbooks, dependencies, RTO/RPO, CDC reconciliation, and customer communications. Availability risks from IAM, KMS, quotas, certificates, DNS, and network policy are tested explicitly.

## 10. Key trade-offs and risks

Regional Cloud SQL HA solves zonal failure but not regional loss; cross-region replication or backup restore determines cost and RPO. Managed CDC reduces custom maintenance but introduces connector, logical-slot, and product limits. At-least-once CDC requires deduplication and reconciliation. A three-zone regional cluster costs more than a zonal cluster but is required for automatic zone survival. The 99.95% target excludes failures outside the agreed service boundary only if contractually documented; capacity, quotas, and dependency failures remain platform responsibilities.