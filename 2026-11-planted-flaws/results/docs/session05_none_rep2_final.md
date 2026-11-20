# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets and end-to-end SLO

- Customer-facing service availability target is 99.95% per month, measured end to end at the global load balancer for valid requests; this defines the error budget.
- Managed-service availability claims are inputs, not additive guarantees of the platform SLO. Capacity, dependencies, failover, and recovery are included in the end-to-end SLO review.
- The platform must survive loss of one zone without operator action.
- Loss of a region has a documented and rehearsed recovery in a second region, with a 15-minute RTO and a 5-minute RPO, subject to measured recovery tests.
- Peak traffic is about 5,000 requests per second. The team is eight engineers on a managed-service budget.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools in all three zones.
- A warm-standby GKE Standard cluster is pre-provisioned in europe-west1 for regional recovery. It includes tested minimum application-serving capacity, system and application node pools, VPC/subnets, Cloud NAT and routing, IAM, secrets/configuration, Cloud SQL connectivity, and a configured global load-balancer backend. Its capacity is validated against the recovery traffic target; recovery cannot depend solely on cold autoscaling.
- Separate system and application node pools use cluster autoscaling.
- Size pod secondary ranges from the maximum node and pod scale, using GKE's actual per-node allocation and headroom; validate the selected range and IP utilization before production and test the documented expansion plan.
- Clusters are VPC-native with private nodes. Control-plane access is limited to authorized networks. Internet egress uses Cloud NAT on a regional Cloud Router.
- Use the GKE Regular release channel (or Extended where justified), with a tested upgrade policy and documented maintenance window. Validate releases in a non-production cluster before production rollout.

## 3. Capacity

- Each API pod serves about 800 requests per second; six replicas provide capacity above the 5,000 requests-per-second peak only if confirmed by load testing.
- Each zone is sized for approximately 60% utilization at peak. After loss of one zone, the remaining zones must sustain traffic within tested capacity while autoscaling adds nodes.
- Load tests must cover peak traffic, dependency failures, zone loss, node replacement, and autoscaler startup time. Define minimum and maximum node counts and alert before regional capacity limits are reached.
- The warm recovery region has pre-provisioned minimum serving capacity and tested scale-out headroom.

## 4. Workload placement and disruption

- Stateless tiers run six replicas, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Required hostname anti-affinity prevents two replicas of a tier from sharing a node where capacity permits; validate that constraints do not prevent recovery or autoscaling.
- Each tier has a PodDisruptionBudget with `minAvailable: 5` (or an explicitly validated equivalent), preserving service during one voluntary disruption without blocking all drains.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, and upgrades are tested against the PDB and available capacity.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use a dependency-appropriate application endpoint, and connection draining is 60 seconds.
- Regional failover uses the load balancer's tested health-based backend failover or traffic controls, not a 3,600-second DNS cutover. Any DNS used for bootstrap or client routing has a bounded TTL and documented resolver-cache limitations.
- Recovery runbooks cover database promotion, application connection cutover, application configuration/secrets, Datastream restart, traffic cutover, validation, and rollback. Traffic switches only after database promotion and application cutover are complete.
- Rehearse regional recovery at least annually and measure the 15-minute RTO, 5-minute RPO, and post-promotion CDC freshness.

## 6. Database

- Cloud SQL for PostgreSQL is regional HA, with automatic failover between zones. Automated backups and point-in-time recovery are enabled.
- The HA standby is not used for reads. Analytics uses a separately provisioned supported read replica, preferably in-region, with lag monitoring and explicit behavior when lag exceeds the reporting objective.
- A cross-region read replica in europe-west1 is the regional-recovery target. Promotion is performed by a documented, tested runbook; measure replication lag and the data-loss window and confirm they meet the 5-minute RPO.
- Backup restore time is size- and configuration-dependent, not assumed to be five minutes. Establish a tested restore RTO, monitor backup success, and use point-in-time recovery for corruption according to the tested procedure.

## 7. Change data capture to BigQuery

- Datastream reads committed changes from Cloud SQL using a supported logical-decoding configuration and writes them to BigQuery without materially endangering primary workload; validate source overhead and capacity.
- Define an end-to-end freshness SLO: committed changes reach queryable BigQuery data within five minutes under normal operation. Alert before the objective is breached, for example at three minutes, and monitor source, stream, and destination lag separately.
- Configure destination processing and staleness/freshness controls consistently with the five-minute objective.
- Processing is idempotent, with documented handling for deletes, updates, duplicates, checkpoints, and replay after regional promotion. Test Datastream restart and failover behavior.
- Monitor replication slots, WAL retention, backlog, and failure handling so CDC cannot exhaust primary storage.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only images built by the approved pipeline.
- Personal-data columns use BigQuery policy tags, and datasets use customer-managed encryption keys. Recovery runbooks include access to keys, secrets, and permissions in the recovery region.

## 9. Observability

- SLIs are load-balancer request success rate and latency, with one-hour and six-hour error-budget burn-rate alerts.
- Dashboards and alerts cover regional backend health, failover state, database HA and replica lag, cross-region RPO, Datastream source/stream/destination lag and freshness, BigQuery availability, node capacity per zone and region, autoscaler state, and PDB/upgrade blockage.
- Alerts have documented ownership, escalation, and tested runbook links.

## 10. Testing and readiness

- Run a zone-failure game day quarterly.
- Run a full regional recovery rehearsal at least annually, including global load-balancer failover, warm-cluster serving capacity, database promotion, application connection cutover, CDC restart and replay, and restoration of observability and access.
- Load-test peak traffic and zone-loss capacity; test upgrades, backup restores, replica promotion, CDC replay, and data correctness.
- Production readiness requires the warm recovery cluster and its networking, NAT, IAM/secrets, Cloud SQL connectivity, minimum serving capacity, and load-balancer backend to be provisioned and tested.
- Record measured RTO, RPO, CDC freshness, restore duration, and failure modes. Do not declare production readiness until the stated SLOs and recovery objectives are demonstrated.