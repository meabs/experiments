# Highly Available GKE Platform and PostgreSQL CDC Design

## 1. Goals, assumptions, and objectives

This platform serves a customer-facing stateless web/API service and message queue in one continent. Peak traffic is approximately 5,000 requests/second. The service target is 99.95% monthly availability. It must survive loss of one zone without operator intervention; regional loss has a documented, rehearsed recovery.

Use managed Google Cloud services suitable for an eight-engineer team. Assume two available regions, application retry and idempotency support, and a defined regional data-loss window. The primary region is sized so either remaining zone can serve critical traffic after one-zone loss.

Targets:

* service availability: 99.95% monthly;
* zonal failure: automatic recovery, no planned data loss;
* regional recovery RTO: 60 minutes;
* regional database RPO: observed cross-region replica or backup lag, capped at five minutes as a target, not guaranteed;
* CDC freshness: at least 99% of committed changes visible in curated BigQuery within five minutes, excluding a declared regional-recovery interval.

Track three recovery points independently:

1. **Database-commit RPO:** commits present on the promoted database.
2. **Durable raw-CDC RPO:** changes durably landed in the raw CDC store.
3. **BigQuery-visibility RPO:** changes applied to curated BigQuery tables.

A database commit may survive promotion without its CDC event having reached raw storage. Recovery reports database and analytics gaps separately.

## 2. GKE topology and workload placement

Use a regional GKE Standard cluster spanning three zones, with private nodes, a restricted private control-plane endpoint, release channels, Workload Identity, managed Prometheus, NetworkPolicy, Shielded Nodes, and Dataplane V2.

Use separate node pools:

* system pool: at least three nodes, distributed across zones, for DNS, metrics, ingress, and platform controllers;
* application pool: autoscaled across all zones;
* queue-worker pool: independently autoscaled and protected from API starvation;
* optional tainted batch pool for migrations and backfills.

Reserve quota and minimum capacity so either remaining zone can carry critical workloads after one zone fails. Prefer stateless pods and managed services; use regional persistent disks only where unavoidable. Define requests, limits, quotas, priority classes, and topology spread constraints across zones and hostnames. Use anti-affinity so replicas do not share a node or zone.

Critical deployments have at least three replicas, startup/readiness/liveness probes, graceful termination, and PDBs allowing one voluntary disruption while preserving service. PDBs must not indefinitely block urgent repairs. Use rolling updates with `maxUnavailable: 0` where capacity permits and adequate surge capacity.

The managed regional queue uses stable message IDs, bounded retention, retry and dead-letter policies, visibility/lease timeouts, and idempotent consumers. Poison messages are isolated and alerted.

## 3. Traffic, networking, and security

Use a global external HTTPS Application Load Balancer with Cloud Armor, managed certificates, WAF/rate limiting, and GKE Gateway/Ingress backends. Health checks must test readiness. Use DNS only for controlled regional failover, not for rapid zone failover.

The standby region contains deployed images/configuration, infrastructure-as-code, secrets, quotas, and warm minimum capacity. Regional traffic switching uses the tested global load-balancer backend/health-check mechanism; the runbook records measured detection and convergence time. If DNS policy is also used, its TTL and measured propagation time are explicitly documented and it is not counted on for the 60-minute target without testing.

Use separate projects for production, networking, security/logging, and analytics. Use custom VPC subnets, secondary pod/service ranges, private Google access, Private Service Connect where supported, Cloud NAT with logging, and default-deny hierarchical/VPC firewall rules. Nodes and databases have no public IPs. Apply namespace NetworkPolicies and restrict egress where practical.

Use least-privilege IAM, groups, MFA, short-lived credentials, Workload Identity, audited break-glass access, Secret Manager, private Artifact Registry, image scanning/signing/attestation, and approved CI/CD deployment. Do not use long-lived service-account keys.

## 4. Cloud SQL PostgreSQL

Use Cloud SQL PostgreSQL regional HA with a synchronous standby in another zone, automatic failover, private IP, automated backups, PITR, WAL archiving, encryption, and deletion protection. Size CPU, storage, IOPS, and connections from load testing with at least 30% measured peak headroom; enable storage autoscaling with an operational ceiling.

Use the Cloud SQL connector with certificate validation, pooling, bounded connection timeouts, and reconnect logic. Retry only safe/idempotent transactions; application operations use idempotency keys. Monitor CPU, memory, storage, connections, locks, transaction latency, autovacuum, failover duration, replication lag, and WAL.

Read replicas serve only explicitly safe read workloads. They are not the source of truth. Migrations use expand/contract sequencing, an explicit lock, backward-compatible application versions, and destructive cleanup only after all consumers migrate.

For regional DR, maintain a cross-region read replica or suitable replicated/PITR backup. Cross-region replication is asynchronous. The measured lag at the last valid observation is the database RPO, with five minutes as the maximum target. The runbook fences writes and the old region, promotes or restores the standby, validates the recovery point and invariants, updates routing/secrets, then enables writes. Reverse replication and return to the original region are planned operations only.

## 5. CDC into BigQuery

Use Datastream or an equivalent managed PostgreSQL logical-replication service. It reads WAL, not application tables, and writes immutable events to a restricted, durable raw landing zone before Dataflow/Dataform transforms them into curated BigQuery tables. Use a dedicated least-privilege replication user, TLS, and a dedicated slot/publication as supported.

Raw events contain source epoch, table, primary key, operation, transaction ID, commit timestamp, LSN or equivalent source position, event ordinal, schema version, and ingestion timestamp. Retain raw events for a bounded period at least as long as the agreed replay/recovery window; use CMEK, restricted access, partitioning, lifecycle deletion, and audit logs.

Delivery is at least once. Duplicates are expected. Ordering is guaranteed only within the transaction/stream semantics provided by the connector; consumers must not assume global ordering across tables. Curated tables use deterministic MERGE/deduplication by source epoch, table, primary key, source position, and event identity. Deletes are tombstones applied according to retention policy. Late events use a bounded correction window.

Monitor source CPU/I/O, WAL generation, slot lag, retained WAL, disk growth, connector lag, raw landing age, Dataflow backlog, BigQuery errors, duplicate rates, schema drift, and curated freshness.

### WAL/slot-overflow emergency runbook

Alert before retained WAL threatens storage. If lag continues to grow:

1. throttle or stop nonessential backfills and heavy analytics;
2. assess connector health and the last durable raw checkpoint;
3. protect primary storage by fencing/recreating the connector from that checkpoint with an overlap, rather than allowing the slot to exhaust disk;
4. assign a new source epoch if the stream is recreated;
5. deduplicate the overlap deterministically;
6. record any source interval that cannot be recovered and reconcile it from the promoted/current database or application records;
7. resume only after WAL and disk headroom are safe.

Do not drop a slot without recording its last confirmed position and an approved recovery plan.

### Initial backfill

Create a consistent PostgreSQL snapshot and record its WAL/LSN position. Establish CDC at that position or an earlier safe position, then load the snapshot in throttled batches. Apply the overlapping CDC stream idempotently after the snapshot load. This prevents updates/deletes during handoff from being lost. Validate row counts, checksums/samples, source-position watermarks, and reconciliation totals before declaring completion.

### Failover and regional recovery

Cloud SQL zonal failover uses the stable instance endpoint. Logical-slot continuity after promotion is a tested dependency, not an assumption. Fence the old connector, record the promotion LSN, and verify whether the slot continues. If not, recreate the stream with a new source epoch and replay an overlap from the last durable raw checkpoint.

For regional recovery, fence the old database, connector, and consumers to prevent split-brain writes. Promote/restore the DR database, record its recovery/promotion LSN and source epoch, establish a new CDC stream, and reconcile from durable raw events plus an overlap. A commit present in the promoted database but absent from raw CDC is reported as an analytics gap; an event absent from both the promoted database and raw landing zone is reported separately as unrecoverable within the stated RPO. BigQuery may contain events beyond the promoted database recovery point; mark the recovery boundary and replay, retract, or correct them.

CDC reconnects after normal Cloud SQL HA failover using the instance endpoint. Test all connector behavior, including slot recreation, overlap, duplicate suppression, and WAL safety, before production.

## 6. Schema and personal data controls

Schema changes use expand/contract: add nullable fields and compatible types, deploy readers/writers, update connector and BigQuery schemas, backfill, then remove old fields only after consumers migrate. Incompatible changes use a versioned stream/table and controlled cutover. Test DDL in staging.

Classify personal data before replication. Replicate only necessary columns; tokenize or hash identifiers where suitable and exclude secrets. Apply CMEK, encryption in transit and at rest, BigQuery policy tags, column-level and row-level controls, separate service accounts, audit logging, retention limits, and restricted exports. Subject deletion must propagate to raw, curated, derived, cached, and temporary data, with an auditable exception process for legally retained immutable records. Never place personal data in logs, metrics labels, dead-letter messages, or incident chat.

## 7. Operations, upgrades, and observability

Use Terraform/IaC, GitOps, policy checks, reviewed environments, signed images, canary/progressive rollout, and automated tests. Upgrade GKE with surge upgrades, spare capacity, and PDB-aware draining. Upgrade PostgreSQL and CDC components in tested maintenance windows with backups and rollback plans. Do not combine unrelated database, cluster, and application changes.

Centralize structured logs, metrics, traces with sensitive-field redaction, and audit logs. Dashboards cover request rate/latency/errors, saturation, per-zone capacity, pending pods, disruptions, load-balancer health, queue age/depth/DLQ, database health/failover/WAL, CDC lag and raw age, BigQuery failures, duplicate rates, and freshness. Use actionable SLO-based alerts and runbooks.

## 8. Failure testing and acceptance

Test zone loss by cordoning/draining or simulating unavailable zones. Verify load-balancer removal, rescheduling, capacity, queue continuity, Cloud SQL failover, connector recovery, and no operator-required service outage.

Run a quarterly regional game day: fence the primary, switch the tested global load-balancer backend, promote the database, fence old consumers/connectors, start CDC with a new epoch, reconcile overlaps, validate application/database invariants, and measure traffic convergence, RTO, database RPO, raw-CDC RPO, and BigQuery visibility RPO. Test backup restoration independently.

Before production demonstrate sustained 5,000 requests/second with headroom, automatic zone survival, measured database failover and CDC recovery, five-minute normal CDC freshness, privacy/deletion verification, successful regional recovery within 60 minutes, tested backup restore, and reviewed dashboards, IAM, runbooks, and change procedures.

## 9. Risks and accepted trade-offs

Regional HA protects against zone failure but does not provide zero-RPO regional resilience. Cross-region replication, raw CDC, and BigQuery are asynchronous and have independently measured recovery points. CDC is at-least-once and eventually consistent; duplicates, late events, corrections, and regional-boundary gaps are expected. A warm standby and reserved capacity cost more than cold recovery but are required for the RTO. Active-active writes are rejected because conflict resolution and personal-data consistency exceed the team’s operational budget.