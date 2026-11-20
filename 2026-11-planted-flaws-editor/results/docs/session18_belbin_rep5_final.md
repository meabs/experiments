# Highly available GKE platform with a Cloud SQL analytics feed: design v3

Written by Agent I, the platform lead.

## 1. Targets and availability

- The customer-facing platform has a 99.95% monthly end-to-end availability SLO, measured at the global load balancer. This allows approximately 22 minutes of monthly error budget.
- Availability is treated as an end-to-end dependency budget; the availability of GKE, Cloud SQL, load balancing, networking, DNS-independent failover, and supporting services is measured and allocated rather than assumed to multiply to 99.95%.
- The platform must serve approximately 5,000 requests per second at peak.
- It must survive loss of one zone without operator intervention.
- Loss of the primary region requires a documented and rehearsed recovery in a second region, with an RTO of 15 minutes and a target RPO of 5 minutes. The achievable RPO is bounded by measured asynchronous replication lag.
- The team consists of eight engineers and uses managed services wherever practical.

## 2. Cluster, regional footprint, and node topology

- The primary production footprint is one regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools distributed across all three zones.
- A recovery regional GKE application footprint is maintained in europe-west1. It includes the required cluster or equivalent managed GKE capacity, system and application node pools, deployed application versions, configuration, secrets, policies, observability, and network connectivity required to serve production traffic after database promotion.
- The recovery footprint is provisioned and sized to meet the 15-minute RTO rather than being created from scratch during an incident. Its capacity, autoscaling, image/configuration/secret synchronization, database endpoint switching, and readiness behavior are tested in regional recovery rehearsals.
- Both regional application footprints are represented as backends of the global external Application Load Balancer. The recovery backend remains unable to receive traffic until its database and application readiness gates have completed.
- Separate system and application node pools use cluster autoscaling. Maximum node counts and per-zone reservations are defined from load tests and failure testing.
- The pod secondary range is sized for the maximum autoscaled node count, GKE per-node allocation overhead, and growth headroom; it is not limited to the nominal initial node count. An initial range such as `/19` is used only after validating the selected per-node allocation and VPC capacity.
- The clusters are VPC-native with private nodes. Control-plane access is restricted to authorised networks. Internet egress uses Cloud NAT through a regional Cloud Router, with NAT capacity and regional failure behavior tested.
- The clusters use the Regular release channel (or Stable if its required features are available), with upgrade testing, rollback procedures, and defined maintenance windows. Production upgrades are staged and observed before broad rollout.
- Container images, configuration, secrets, IAM bindings, policies, and infrastructure changes are synchronised to the recovery footprint through the approved deployment pipeline. Synchronisation status is monitored and is a prerequisite for declaring the recovery region ready.

## 3. Capacity

- Load testing establishes API-pod throughput, resource requests, limits, and scaling behavior. The initial deployment uses at least eight API replicas, rather than relying on six replicas at 800 requests per second.
- Node pools are sized with sufficient spare capacity for normal bursts, rolling upgrades, disruption budgets, and loss of any one zone. Post-zone-loss utilisation must leave verified headroom for scheduling and autoscaler scale-out; approximately 90% utilisation is not accepted without demonstrated recovery margin.
- The primary and recovery regional footprints are each tested for the capacity required during their intended operating mode, including regional recovery traffic.
- Capacity assumptions and autoscaler behavior are validated in peak-load and zone-loss tests.

## 4. Workload placement and disruption

- Stateless tiers run at least eight replicas, distributed across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Required hostname anti-affinity is used where no two replicas of a tier may share a node. Scheduling rules are tested against the actual node-pool capacity.
- Each tier has a PodDisruptionBudget that preserves the tested maintenance availability target while permitting voluntary disruption; for an eight-replica tier, the initial policy is `minAvailable: 7`, subject to upgrade and zone-failure validation.
- Node pools use surge upgrades, initially `maxSurge: 1` and `maxUnavailable: 0`, with upgrade duration and capacity impact measured.
- PDBs do not substitute for adequate spare capacity or zone-aware placement.

## 5. Traffic and regional failover

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use a readiness-aware endpoint that verifies that the regional application is able to serve traffic and does not route requests to an unpromoted or read-only database.
- Regional failover uses health-based global load-balancer backend failover, not a one-hour DNS change. Failover detection and connection draining are tested against the 15-minute RTO. DNS is not relied upon for the recovery deadline.
- Regional recovery is one coordinated runbook: detect and declare the regional failure, fence writes and prevent split brain in the failed region, promote the cross-region Cloud SQL replica, switch application database endpoints/configuration, validate the promoted database and application readiness, validate that the recovery footprint is synchronised and has sufficient capacity, and only then enable or prefer the recovered region's load-balancer backend.
- The recovery backend remains unhealthy to the load balancer until write fencing, replica promotion, endpoint switching, and all application dependency checks succeed.
- The runbook records replication lag and the expected data-loss boundary, and is rehearsed at least annually. The complete sequence must meet the 15-minute RTO and demonstrate the five-minute RPO target under tested lag conditions.

## 6. Database

- Cloud SQL for PostgreSQL in europe-west2 uses high availability, with a primary and a standby in separate zones and automatic intra-region failover.
- The HA standby is not used for analytics. Dashboards use a separately provisioned supported Cloud SQL read replica (or an explicitly approved equivalent), sized for reporting load and monitored for lag, errors, and failover behavior.
- Automated backups and point-in-time recovery are enabled.
- A cross-region asynchronous read replica in europe-west1 is the regional recovery target. Replication lag is monitored with promotion criteria and alerts. The measured lag determines whether the five-minute RPO target is currently achievable.
- Promotion, endpoint switching, write fencing, and rollback are documented and tested. Asynchronous replication can lose commits made after the last replicated position; that data-loss boundary is explicitly reported during recovery.
- Backup restoration is not assumed to take a fixed time. Restore and validation objectives are measured against the actual database size and workload during recovery tests, and the results are recorded alongside backup retention and PITR objectives.

## 7. Change data capture to BigQuery

- Datastream reads changes from the Cloud SQL primary using a supported logical-decoding configuration and writes them to BigQuery without using the analytics read replica unless explicitly validated.
- The target is for every committed change to reach BigQuery within approximately five minutes. Freshness is measured end to end, and alerts fire at three minutes.
- Replication slots, WAL growth, CPU, storage, I/O, and primary-database latency are monitored. Slot/WAL growth has bounded thresholds and an operational response so CDC cannot endanger the primary.
- Any BigQuery destination staleness or partitioning controls are configured for cost management only if they do not prevent the approximately five-minute end-to-end freshness objective. A nominal 15-minute destination staleness limit must not silently override that objective; if it is retained for a specific workload, the affected dashboard freshness behavior, exception, and alerting are explicitly documented.
- Events are applied idempotently, for example by merging on a stable primary key and event/version semantics, so retries and duplicate delivery do not create duplicate current rows. Reconciliation detects missed or out-of-order changes.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default.
- Binary Authorization admits only images built and attested by the approved pipeline.
- Personal-data columns in BigQuery use policy tags, and datasets use customer-managed encryption keys. Key access, rotation, and recovery procedures are tested.

## 9. Observability and error budget

- SLIs are load-balancer request success rate and latency, with burn-rate alerts over one-hour and six-hour windows.
- Dashboards show regional backend health, database promotion state, replication lag and achievable RPO, read-replica lag, Datastream freshness, replication-slot/WAL growth, node capacity by zone, autoscaler state, PDB/upgrade status, recovery-footprint synchronisation, and recovery-region readiness.
- The end-to-end SLO has an explicit dependency and error-budget analysis. Incidents, maintenance, and failover tests consume the measured budget and trigger corrective action when burn rates exceed policy.

## 10. Testing and build gates

- Before production, load tests validate peak throughput, eight-replica capacity, autoscaling, and post-zone-loss headroom.
- Both regional application footprints are tested for image, configuration, secret, policy, networking, capacity, and readiness synchronisation.
- Upgrade and drain tests validate PDBs, surge capacity, topology spread, and rollback.
- A zone-failure game day runs quarterly.
- A full regional recovery rehearsal runs at least annually and includes recovery-footprint readiness, write fencing, replica promotion, endpoint switching, load-balancer failover, replication-lag/data-loss recording, and timing against the 15-minute RTO and five-minute RPO.
- Datastream load, WAL impact, duplicate handling, freshness, and recovery behavior are tested.
- Backup restore and PITR times are measured at representative database sizes.
- Build approval requires passing these tests and recording the resulting capacity, availability, restore, promotion, synchronisation, and RPO measurements.