# Highly available GKE platform with a Cloud SQL analytics feed: design v3

Written by Agent I, platform lead.

## 1. Targets

- Service availability target: 99.95% per month (about 22 minutes), measured at the load balancer.
- Peak traffic is approximately 5,000 requests/second. The team is eight engineers and prefers managed services.
- The platform must survive loss of one zone without operator intervention.
- Loss of the whole region requires a documented and rehearsed recovery in a second region, with a 15-minute RTO and 5-minute RPO.
- Availability analysis includes dependencies, failure capacity, and tested failover paths; individual managed-service availability figures are not summed as proof of the platform target.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with a control plane replicated across three zones and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled.
- The pod secondary range is at least /20, with documented expansion capacity and quota checks. Capacity planning includes node and pod headroom, not only nominal per-node pod count.
- The cluster is VPC-native with private nodes. Control-plane access is limited to authorised networks. Internet egress uses Cloud NAT through a regional Cloud Router.
- The Regular production release channel is used (Stable may be selected if required features are available). Upgrades are tested before production rollout and use a weekly Sunday 02:00–06:00 local-time maintenance window, subject to emergency security maintenance.

## 3. Capacity

- Each API pod serves approximately 800 requests/second under representative load. Six replicas therefore exceed the 5,000-request/second peak, with requests and limits validated by load testing.
- Capacity and quotas are provisioned so loss of one zone leaves guaranteed scheduling headroom in the remaining zones. The target of 90% utilisation after zone loss is a maximum to validate, not a capacity guarantee; overhead, autoscaler latency, and rollout capacity are included.
- Autoscaler scale-up, pod startup, and quota behavior are tested during zone-failure exercises.

## 4. Workload placement and disruption

- Stateless tiers run six replicas, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Preferred hostname anti-affinity is used; it intentionally permits co-location, so capacity and placement are verified in scheduling tests.
- Each tier has a tested PodDisruptionBudget, initially `minAvailable: 5`, so voluntary maintenance can proceed without eliminating all disruption capacity. The budget is not a substitute for spare capacity.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`. Upgrade and drain procedures are tested against the availability objective.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use an application endpoint that verifies readiness and required dependencies without destructive operations. Connection draining is 60 seconds.
- europe-west1 has a continuously provisioned, deployed, and tested GKE recovery deployment. Its quotas, node capacity, headroom, and application configuration are validated and maintained between rehearsals; it is not merely a load-balancer backend or deployment procedure.
- Regional failover uses the load balancer’s health-based failover and is exercised during recovery rehearsals. DNS is not the primary failover mechanism. Any DNS records used for clients have a substantially reduced TTL with documented resolver and client-cache limitations.
- The recovery runbook sequences traffic switching, database promotion, application write-endpoint reconfiguration, Datastream/CDC continuity, and post-cutover validation. Its measured completion time must be 15 minutes or less.

## 6. Database

- Cloud SQL for PostgreSQL runs in europe-west2 with HA enabled: a primary and standby in separate zones, with automatic regional failover.
- The HA standby is not used for reporting. Dashboards use a separately provisioned, supported read replica or another dedicated analytics path, and reporting load is tested not to endanger the primary.
- A cross-region read replica in europe-west1 is the regional-recovery target. Replication lag is monitored and paged. Promotion is documented and tested, and must provide an achievable RPO of five minutes or less and RTO of 15 minutes or less.
- Automated backups and point-in-time recovery are enabled. Restore timing is size- and workload-dependent and is measured in regular tests; no unconditional five-minute restore guarantee is made.
- Data-loss and split-brain safeguards, promotion ordering, connection reconfiguration, and post-promotion validation are included in the runbook.

## 7. Change data capture to BigQuery

- Datastream uses a supported PostgreSQL logical-decoding configuration and writes to BigQuery. Before production, the team verifies flags, privileges, replication slots, retention behavior, supported versions, and measured primary I/O/storage impact.
- Target freshness is five minutes, with alerts at three minutes. Monitoring covers source availability, slot/WAL growth, stream errors, lag, BigQuery load errors, and behavior during Cloud SQL failover and regional promotion.
- The BigQuery staleness limit is 15 minutes only if compatible with the five-minute committed-change requirement; otherwise it is reduced. The operational target remains about five minutes.
- Events are applied idempotently, with replay and duplicate handling documented. Backlogs and recovery are tested without endangering primary storage.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only approved-pipeline images.
- Personal-data columns use BigQuery policy tags; datasets use customer-managed encryption keys. Key availability and permissions are included in regional-recovery testing.

## 9. Observability

- SLIs are request success rate and latency measured at the load balancer. Alerts cover one-hour and six-hour error-budget burn rates.
- Dashboards and alerts cover replication lag, CDC freshness, slot/WAL growth, backup status, restore tests, node-pool capacity by zone, quotas, autoscaler state, load-balancer health, and failover status.
- Alerts have documented owners, runbooks, and escalation paths.

## 10. Testing and acceptance

- A quarterly zone-failure game day verifies no operator intervention is required, sufficient remaining capacity, and application SLO behavior.
- At least annually, a full regional recovery rehearsal measures the complete sequence: recovery-region GKE capacity, traffic switching, database promotion, application write-endpoint reconfiguration, Datastream behavior, validation, RPO, and RTO. The recovery region’s continuously provisioned deployment, quotas, node capacity/headroom, and maintained application configuration are acceptance criteria.
- Before build approval, load, upgrade, disruption, backup-restore, Cloud SQL failover, Datastream failover, and cross-region promotion tests establish the stated claims.
- Production approval requires measured evidence that the 99.95% objective is credible and the 5-minute RPO and 15-minute regional RTO are achievable.