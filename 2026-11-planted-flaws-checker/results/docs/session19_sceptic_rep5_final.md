# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets

- The end-to-end availability SLO is 99.95% per calendar month for successful customer requests, measured at the global load balancer. This allows approximately 22 minutes of unavailability per month.
- The design must tolerate loss of one zone without operator intervention.
- Loss of the primary region must have a documented and rehearsed recovery, with a target RTO of 15 minutes and a target RPO of 5 minutes. These targets are validated by testing rather than assumed from provider component availability.
- Peak traffic is approximately 5,000 requests per second. The team consists of eight engineers, so the design uses managed services and avoids unnecessary operational components.
- Availability budgets cover the complete request path, including GKE, load balancing, Cloud SQL, networking dependencies, and failover procedures. Individual managed-service SLAs are not multiplied to claim the end-to-end SLO.

## 2. Cluster and node topology

- Use one regional GKE Standard cluster in `europe-west2`, with the regional control plane and node pools distributed across all three zones.
- Use separate system and application node pools. Both use cluster autoscaling and have explicitly tested minimum and maximum sizes per zone.
- Use VPC-native networking with private nodes. Size the pod secondary range for the maximum node count, GKE per-node allocation, and growth. A `/18` is the initial allocation for the planned capacity (subject to confirmation against the selected `maxPodsPerNode` and GKE allocation settings); a `/22` is not sufficient for 30 nodes at 110 pods per node.
- Record the actual `maxPodsPerNode`, per-node secondary-range allocation, maximum node count including surge, and measured address consumption. Reserve address space and an expansion procedure for future growth. Confirm effective pod IP consumption in a capacity test before production.
- Limit control-plane access to authorised networks. Internet egress uses Cloud NAT and a regional Cloud Router; NAT capacity and port exhaustion are monitored.
- Use the Regular GKE release channel for production, with a tested upgrade process, maintenance exclusions where appropriate, and rollback or mitigation procedures. Do not use Rapid on the basis that it is the most stable channel.
- Set a weekly maintenance window, initially Sunday 02:00–06:00 local time, and verify that it is compatible with the service error budget.

## 3. Capacity

- The current estimate is that one API pod serves approximately 800 requests per second. Start with at least 12 replicas, distributed evenly across zones where possible, rather than relying on eight replicas alone. Validate the estimate with representative load tests.
- Define CPU, memory, and request-rate resource requests and limits for every workload. Autoscaling uses measured CPU/memory and, where needed, an application request-rate metric.
- Size every zone so that the remaining two zones have tested capacity for peak traffic after losing one zone, including at least eight immediately serviceable API replicas for the 12-replica baseline, pending-pod scheduling, image pulls, and autoscaler delay. Demonstrate 5,000 requests per second during the failure test; do not rely on unmeasured autoscaler response.
- Set node-pool maximums high enough for the one-zone-loss scenario and verify quotas, IP capacity, and regional compute capacity.

## 4. Workload placement and disruption

- Run stateless tiers with at least 12 replicas, using required topology spread constraints across zones (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Use required hostname anti-affinity, or an equivalent placement policy, when the tier requires no two replicas on one node. A preferred anti-affinity rule is not a guarantee.
- Set each tier's PodDisruptionBudget to a value that preserves service while permitting maintenance; initially use `minAvailable: 11` for 12 replicas, subject to validation of the rollout and zone-loss behaviour. Do not set `minAvailable` equal to the replica count.
- Use node-pool surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to confirming that quotas and the PDB allow upgrades to complete.
- Test voluntary drains, upgrades, autoscaler scale-up, and a zone failure before production.

## 5. Traffic and regional recovery

- Use a global external Application Load Balancer with regional backends and health checks that test application readiness, not merely process liveness. Use connection draining of 60 seconds unless testing requires a different value.
- Configure health-based backend failover so that traffic is removed from an unhealthy region without depending on DNS changes.
- Keep a pre-provisioned recovery GKE cluster or warm recovery capacity in the recovery region, with verified quotas, nodes, images, configuration, secrets, Binary Authorization readiness, and load-balancer backend registration. A cold-cluster path is not acceptable unless complete provisioning, registration, and readiness are measured and demonstrated to fit the 15-minute RTO.
- The regional recovery runbook must include provisioning or selecting the recovery capacity, promoting the database, switching application database configuration, handling Datastream state, fencing the old primary, validating application health, and directing traffic to the recovery region.
- DNS is not the primary failover mechanism. If DNS is used for any auxiliary endpoint, use a low, tested TTL and document resolver caching limitations; a 3,600-second TTL cannot support a 15-minute RTO.

## 6. Database

- Use Cloud SQL for PostgreSQL with regional high availability enabled. The HA standby is for failover and is not treated as a readable analytics endpoint.
- Serve dashboards from a separately provisioned, supported Cloud SQL read replica or from BigQuery. The read replica has defined size, query limits, lag monitoring, and a documented failure/maintenance procedure so analytics cannot exhaust primary capacity.
- Maintain a cross-region read replica in `europe-west1` as the regional recovery target. Monitor replication lag continuously and alert before the five-minute RPO objective is threatened.
- The recovery runbook must specify the promotion point, acceptable data loss, promotion procedure, application endpoint update, old-primary fencing, and post-promotion validation. A replica does not by itself guarantee a five-minute RPO.
- Enable automated backups and point-in-time recovery. Do not claim a fixed restore time regardless of database size. Measure restore time with a representative database and record the tested RTO, including validation and application reconnection. Use the cross-region replica for regional recovery where appropriate; use backup/PITR for corruption recovery.
- Perform regular promotion, restore, and failback exercises and update the measured RTO/RPO.

## 7. Change data capture to BigQuery

- Datastream reads committed changes from Cloud SQL using a supported logical-decoding configuration and writes them to BigQuery. The target freshness is approximately five minutes, with an alert at three minutes.
- Monitor Datastream lag, errors, slot/WAL retention, storage growth, and primary-database resource impact. Define a bounded-lag response, including pausing or reconfiguring the pipeline before WAL retention threatens the primary.
- During Cloud SQL HA failover or regional promotion, preserve or deliberately recreate the replication slot/checkpoint, reconfigure the connector to the promoted primary, and document the temporary freshness/data-loss behavior.
- Use an idempotent destination design. Merge or deduplicate on a stable primary key and change sequence so retries and replay do not create duplicate current-state rows; define handling for deletes, out-of-order events, schema changes, and reconciliation against the promoted source.
- Set the BigQuery freshness/staleness policy to meet the five-minute committed-change requirement. Cost controls must not permit data to exceed the agreed freshness objective without an alert and documented response.

## 8. Security

- Use Workload Identity Federation for GKE, with one appropriately scoped Google service account per tier and no exported service-account keys.
- Deny cross-namespace traffic by default with network policies, then allow only documented service flows.
- Use Binary Authorization so that only images built and attested by the approved pipeline are admitted.
- Apply BigQuery policy tags and IAM controls to personal-data columns. Use customer-managed encryption keys where required, with monitored key access and rotation procedures.

## 9. Observability and operations

- Measure request success rate and latency at the load balancer and define the SLI filters, sampling, and excluded responses explicitly.
- Alert on one-hour and six-hour error-budget burn rates, regional backend health, database failover status, cross-region replica lag, read-replica lag, Datastream freshness and WAL retention, node capacity by zone, NAT exhaustion, and autoscaler failures.
- Keep dashboards and runbooks for regional failover, database promotion, corruption recovery, CDC lag, and GKE upgrades.
- Attribute the end-to-end error budget to application, GKE, load balancing, database, networking, and operational recovery causes rather than assigning each managed service an independent 99.95% target.

## 10. Testing and acceptance

- Before production, perform load tests at and above 5,000 requests per second, including one-zone loss and autoscaler scale-up. The zone-loss test must demonstrate at least 5,000 requests per second with the surviving capacity.
- Perform a quarterly zone-failure game day and a yearly full regional-recovery rehearsal, measuring the complete path from failover detection through pre-provisioned application readiness, load-balancer routing, database promotion, endpoint switching, Datastream reconfiguration/reconciliation, and validation. The measured result must meet the 15-minute RTO and five-minute RPO.
- Test GKE upgrades and voluntary node drains with the PDB and surge settings.
- Test Cloud SQL HA failover, cross-region replica promotion, fencing, application reconnection, backup/PITR restore, and measured recovery times.
- Test Datastream backpressure and recovery, including slot/checkpoint handling, duplicate/replay behavior, promotion reconfiguration, reconciliation, and confirmation that primary-database performance and WAL retention remain within defined bounds.
- The platform is approved for build only after these tests confirm the stated availability, capacity, freshness, RTO, and RPO objectives.