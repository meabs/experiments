# Highly available GKE platform with a Cloud SQL analytics feed: design v5

## 1. Targets and acceptance criteria

- Customer-facing stateless web/API service, with peak traffic of approximately 5,000 requests/second.
- Monthly end-to-end availability objective is 99.95%, measured at the load balancer for valid requests. The error budget covers load balancing, GKE, Cloud SQL, networking, dependencies, deployments, and operational failover; component SLAs are inputs only.
- The service must continue without operator action after loss of one zone.
- Regional loss has a documented and rehearsed recovery with a 15-minute RTO and measured RPO of no more than five minutes. The RPO claim is conditional on observed cross-region replica lag and is withdrawn or escalated when lag exceeds five minutes.
- Every committed database change should reach BigQuery within five minutes during normal operation. Fifteen minutes is an incident threshold, not the freshness objective.
- Production approval is blocked until the recorded pre-production measurements meet all stated availability, capacity, RTO, RPO, and CDC gates.

## 2. Explicit build parameters and topology

- One regional GKE Standard cluster in `europe-west2`, with the control plane replicated across three zones and node pools in all three zones.
- Separate system and application node pools, both autoscaled. The application pool is capped at **36 nodes, including a two-node upgrade surge**. The system pool has a separate explicit cap of six nodes, including surge.
- The cluster is VPC-native with private nodes. Reserve pod secondary range `/18`. With GKE alias-IP allocation of one `/24` block per node at the selected maximum-pods setting, this provides 64 `/24` blocks: 36 are allocated to the application pool and six to the system pool, for **42 allocated blocks and 22 remaining** for overhead and growth. Apply a **70% total-allocation alarm** and maintain a documented secondary-range expansion plan. The exact GKE allocation is verified before cluster creation; any mismatch blocks deployment.
- Control-plane access is restricted to authorised networks. Internet egress uses regional Cloud NAT and Cloud Router.
- Use the Regular GKE release channel. Upgrades are tested in staging, then rolled out during a documented maintenance window with timezone, surge settings, monitoring, and rollback/recovery procedures.

## 3. Capacity and placement

- Start with at least eight API replicas. The selected planning rate is 800 requests/second per replica, but production approval requires a recorded representative-load result above 5,000 requests/second with required headroom.
- Each zone is provisioned so that, after losing one zone, the two remaining zones can serve 5,000 requests/second without waiting for autoscaler convergence. Tests record per-pod capacity, surviving replica count, node capacity, autoscaler scale-up time, and headroom.
- Application tiers use at least eight replicas, topology spread constraints across zones (`maxSkew: 1`, `DoNotSchedule`), and required hostname anti-affinity where one replica per node is required. The 36-node cap and available nodes must make these constraints schedulable, including during zone loss and upgrades.
- Each tier uses a tested PDB, initially `minAvailable: 7` for eight replicas. It must permit controlled maintenance while preserving tested serving capacity and must not block involuntary or emergency failure recovery indefinitely.
- Node pools use surge upgrades with `maxUnavailable: 0` and an explicitly selected, tested `maxSurge`. Readiness probes, graceful termination, and connection draining prevent terminating pods from receiving new traffic.
- HPA and cluster autoscaler thresholds and scale-up timing are tested with representative workload.

## 4. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with independently health-checked backends in both regions. Health checks use a readiness-oriented endpoint that verifies the serving process and required local dependencies.
- Regional failover is health-based at the load balancer, not dependent on a 3,600-second DNS TTL. Any DNS used has a controlled TTL, but resolver caching is not assumed to satisfy the RTO.
- The secondary region has a deployable application environment, required images, configuration, secrets, capacity reservations, and a tested database endpoint.
- Load-balancer failover must not direct writes to an unpromoted database. The runbook fences or declares the failed primary, isolates stale-primary write access, promotes the cross-region Cloud SQL replica, updates endpoints and configuration/secrets, validates writes, restarts or resumes Datastream from its checkpoint, and only then enables secondary-region write traffic.
- The regional rehearsal records detection, fencing, promotion, configuration, startup, routing, CDC recovery, and validation times. The combined result must be within 15 minutes.

## 5. Database

- Cloud SQL for PostgreSQL with regional HA enabled provides the transactional primary and automatic in-region failover. Its HA standby is not used for reads.
- Analytics uses a separately sized Cloud SQL read replica, initially **4 vCPU, 16 GiB RAM, and 1 TB storage**, with independent monitoring for lag, capacity, connections, availability, and query impact. Dashboards cannot overload the primary. Resize triggers are recorded CPU, connection, query-latency, and lag thresholds.
- A cross-region asynchronous read replica in `europe-west1` is the regional recovery target. Lag is continuously monitored and is part of the conditional five-minute RPO claim. Promotion, endpoint changes, application verification, and measured RPO are rehearsed.
- Backups and point-in-time recovery remain enabled. Restore RTO is database-size- and load-dependent and is stated only from measured rehearsals. Restore tests include integrity checks and application recovery.
- Migration, failover, replica promotion, fencing, and rollback procedures are rehearsed.

## 6. Change data capture to BigQuery

- Datastream uses PostgreSQL logical decoding with all required privileges, publication and replication-slot settings, and WAL-retention controls.
- The logical replication slot, WAL volume, primary storage, Datastream health, and end-to-end freshness are monitored. Safeguards alert and throttle or stop unsafe operation before retained WAL can exhaust primary storage.
- The normal freshness objective is five minutes, with alerts before five minutes and a 15-minute hard incident threshold. Peak-load tests must demonstrate the objective without unacceptable primary overhead.
- BigQuery merge processing is idempotent using a stable source key/event identity. Checkpoint, retry, duplicate, and out-of-order behavior are documented.
- Regional recovery includes Datastream checkpoint/restart handling. The rehearsal verifies no unacceptable loss of committed changes and bounded, explicitly tolerated duplicates.

## 7. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one least-privilege Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only images built and signed by the approved pipeline.
- Personal-data columns use BigQuery policy tags. Datasets use customer-managed encryption keys with documented rotation and recovery access.

## 8. Observability and operations

- SLIs are load-balancer request success rate and latency, with dependency indicators for database errors, saturation, replica lag, CDC freshness, and failover readiness.
- Alerts use one-hour and six-hour error-budget burn rates, plus actionable alerts for zone capacity, autoscaler state, scheduling failures, pod-range capacity, Cloud SQL lag, WAL retention/storage, Datastream lag, and BigQuery freshness.
- Dashboards show per-zone capacity, remaining pod-range capacity, database/CDC state, regional readiness, and current fencing/recovery state.
- Runbooks cover zone failure, regional failover, database promotion, restore, CDC restart, credential/secrets recovery, and rollback.

## 9. Mandatory production gates

Before production approval, recorded test results must demonstrate:

1. At least 5,000 requests/second with the required latency and availability objective.
2. Uninterrupted service after loss of any one zone, including sufficient surviving replicas and node capacity without relying on autoscaler convergence.
3. Successful scheduling with required spread, hostname anti-affinity, PDB, 36-node cap, and upgrade-surge settings.
4. Regional recovery within 15 minutes, including fencing, Cloud SQL promotion, endpoint/configuration and secret changes, application startup, routing, write validation, and Datastream recovery.
5. Measured cross-region database RPO of no more than five minutes, conditional on and continuously supported by replica-lag observations.
6. Normal BigQuery freshness of no more than five minutes under representative peak load, with the 15-minute value treated only as an incident threshold.
7. Restore, failover, rollback, and CDC tests with integrity checks and documented duplicate/loss behavior.
8. Recorded availability-budget and error-budget results meeting the 99.95% end-to-end objective.

A quarterly zone-failure game day and at least annual regional recovery rehearsal are required after launch.