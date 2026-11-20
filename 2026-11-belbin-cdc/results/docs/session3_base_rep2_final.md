# Highly Available GKE Platform and CDC Design

## Goals and assumptions

Serve a stateless web/API service and queue for one continent, peaking at 5,000 requests/s. Target availability is 99.95% monthly, including dependencies where practical. Loss of one zone must recover automatically; regional loss has an operator-led, rehearsed recovery. Cloud SQL PostgreSQL is the system of record. At least 99% of committed changes must be queryable in curated BigQuery tables within five minutes normally. CDC is at-least-once and consumers tolerate duplicates. Regions, quotas, residency, retention, RTO/RPO, and capacity must be validated by load testing.

## GKE and workload topology

Use a private, regional GKE Standard cluster spanning three zones, with regional managed control planes, VPC-native alias IPs, private Google access, and Workload Identity. Use separate tainted node pools and service accounts for system, API/web, workers, and queue consumers. Spread nodes and pods across zones with topology constraints and anti-affinity. Maintain minimum capacity in every zone and N+1 headroom for loss of one zone; reserve capacity where justified.

Critical workloads have at least two replicas, realistic startup/readiness/liveness probes, PDBs, graceful draining, and rolling updates with maxUnavailable zero or a tested small percentage. PDBs protect voluntary disruption but do not prevent zone loss. HPA uses CPU and request/concurrency or latency metrics; cluster autoscaler is quota- and scale-time-tested. Queue consumers scale from backlog with a database-protecting upper bound. Use timeouts, bounded retries with jitter, circuit breakers, rate limits, and idempotency keys.

Use regional managed Pub/Sub with retention, dead-letter topics, ordering keys only where needed, and explicit duplicate handling. Kubernetes does not host PostgreSQL or the durable queue. Use an outbox or equivalent transactional publication pattern where a database action and message must be atomic. Retain the database outbox through the full regional recovery and reconciliation window.

## Traffic and networking

Use a global external HTTPS load balancer with preconfigured primary and recovery-region backends, TLS certificates, health checks, Cloud Armor WAF/DDoS/rate controls, and a GKE Gateway/Ingress. Health-based steering is automatic for endpoint failure; regional disaster steering is an authorized, documented manual operation. DNS is not the sole regional failover mechanism. Configure connection draining and bounded timeouts.

Use Shared VPC or equivalent separation, private nodes, secondary ranges, redundant Cloud NAT, private Cloud SQL connectivity, and restricted egress. Firewall rules and NetworkPolicy are default-deny with explicit service flows. Monitor quotas, NAT ports, IP ranges, and connection limits.

## Transactional database

Use Cloud SQL PostgreSQL HA with a regional synchronous standby in another zone, automatic failover, private IP, PITR, WAL retention, regional backups, deletion protection, and CMEK where required. Size and load-test for peak traffic, failover, CDC overhead, and at least 30% tested headroom. Tune indexes, vacuum/autovacuum, and connection limits.

Applications use the stable Cloud SQL connector endpoint and bounded pooling. Retry only safe/idempotent operations after connection reset. Expect a brief write interruption during failover and include it in the SLO. Use least-privilege roles, encryption in transit and at rest, auditing, and isolated restore tests. Copy immutable backups/exports to the recovery region/project. The regional disaster RPO is the latest replicated backup/WAL boundary, not assumed zero.

## CDC pipeline

Select and validate one architecture: Datastream reads PostgreSQL logical decoding from a dedicated least-privilege replication user/publication and writes immutable change files to dual-region Cloud Storage staging with 30-day retention; Dataflow reads the staging files and writes BigQuery raw and curated tables. Dataflow checkpoints durably and can replay from the last validated object/LSN. Load-test the complete Datastream-to-Cloud-Storage-to-Dataflow-to-BigQuery path to demonstrate the five-minute freshness SLO under expected peak load and failure/replay conditions. Storage is regionally appropriate and available to the recovery procedure.

Enable only logical-replication settings supported by the selected Cloud SQL and Datastream versions. The publication contains only approved tables and columns. Monitor source CPU/I/O, slot lag, WAL retention and disk, connector lag, staging age, Dataflow throughput/errors, BigQuery quotas, and freshness. Alert well before WAL exhaustion; under incident procedure pause or reduce CDC scope to preserve OLTP.

Initial load uses a consistent snapshot, bounded/throttled chunks, and a recorded snapshot watermark while CDC capture is active. Validate counts/checksums and publish only after reconciliation. Never run an unbounded production scan.

Raw records include source table, primary key, operation, transaction identifier, commit timestamp, LSN or equivalent ordering token, operation sequence, schema version, and ingestion time. Delivery is at-least-once. Dataflow replay is safe. Curated tables use idempotent MERGE logic and apply an event only when its source ordering token is newer than the stored token. Event identity includes source transaction/LSN plus operation sequence, not merely primary key. This handles updates, duplicates, late events, and delete/reinsert cycles. Deletes create curated tombstones retained for the replay and verification period; raw retention and personal-data erasure are governed separately.

Ordering is preserved only where the connector exposes it (normally per key/table or transaction); no global ordering is promised. Schema changes use expand/contract: add nullable fields, deploy compatible consumers, backfill, then remove or change fields after retention and review. Unsupported DDL pauses or quarantines affected data rather than silently corrupting it.

The five-minute freshness SLO is measured from source commit time to queryable curated-row time; target 99% of five-minute windows, alert at three minutes and page at five. Personal data is minimized, excluded or masked/tokenized where possible, encrypted, access-controlled with separate analytics identities, policy tags and row/column security, audited, and subject to retention and verified deletion propagation in raw and curated data.

## Failover and disaster recovery

During Cloud SQL HA failover, Datastream reconnects through the primary endpoint. Logical replication slot continuity is not assumed: for the selected versions/configuration, test whether the slot survives promotion. Record the last durable staged LSN. If necessary, recreate the slot on the promoted primary, replay from the recorded position, reconcile overlap, and quantify any unrecoverable gap before declaring freshness restored. Never create an untracked second slot.

Zone loss removes unhealthy endpoints, reschedules pods, uses N+1 capacity, fails Cloud SQL to its standby, and redelivers retained queue messages without human action.

Set a regional target of four-hour RTO and 15-minute RPO, subject to tested backup/WAL replication. On regional loss, fence the old region and ensure only one writable region. Declare recovery, manually steer the preconfigured global load balancer, deploy GKE from IaC, restore secrets/configuration, and restore or promote Cloud SQL from the newest valid cross-region recovery point. Recreate queue consumers.

Pub/Sub is regional and is not assumed to be cross-region replicated. Unacknowledged or retained messages are replayed where possible. Acknowledged messages are preserved only when their database effects or outbox records are covered by the selected recovery point; otherwise they may be lost within the 15-minute RPO. Reconcile or reissue such work from the retained database outbox, with idempotent consumers.

Record the database recovery watermark and last CDC LSN, recreate the Datastream slot and staging path in recovery, replay retained overlap, and reconcile gaps and duplicates into the existing or designated BigQuery dataset. Analytics is marked stale or suspended until continuity is verified. Measure actual RTO/RPO and CDC recovery; do not claim zero loss without evidence.

## Operations, security, and testing

Manage infrastructure, IAM, firewall, GKE, database settings, dashboards, alerts, and policies through reviewed version control and CI/CD. Pin, scan, sign, and verify images. Use supported GKE release channels, maintenance windows, surge upgrades, canaries, rollback, and PDB-aware testing. Test Cloud SQL patches and connector/Dataflow changes separately.

Centralize logs, metrics, traces, and audit logs. Dashboard availability, latency, errors, scheduling, zone capacity, autoscaling, load-balancer health, queue age/DLQ, database saturation/failover, CDC LSN/WAL/freshness/errors/duplicates, BigQuery quotas, and certificate/key expiry. Page on SLO burn, endpoint loss, imminent WAL exhaustion, and freshness breach.

Use separate production, recovery, analytics, and CI projects where practical; least privilege, MFA, short-lived access, audited break-glass, Secret Manager, Workload Identity, key-rotation monitoring, binary authorization, vulnerability scanning, and runtime detection. Ensure IAM or key failure cannot block failover or recovery.

Before production inject zone/node/pod failures, Cloud SQL failover, connector interruption, slot loss, duplicate/reordered CDC, WAL pressure, staging/Dataflow/BigQuery outage, schema incompatibility, queue redelivery, quota failure, expired certificates/secrets, and regional routing loss. Perform at least semiannual isolated regional restores and an annual full failover rehearsal, measuring RTO, RPO, queue treatment, privacy controls, reconciliation, and CDC freshness.