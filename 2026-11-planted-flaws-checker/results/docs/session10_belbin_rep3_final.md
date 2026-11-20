# Highly available GKE platform with a Cloud SQL analytics feed: design v4

## 1. Targets and availability

- Customer-facing stateless web/API service, with peak traffic of about 5,000 requests/second.
- End-to-end monthly availability SLO is 99.95% (about 22 minutes of error budget). This is not derived by multiplying identical component targets. The error budget is allocated across load balancing, GKE/workload capacity, database availability, and operational changes, with dependency and failover assumptions documented and reviewed.
- The platform must continue serving without operator intervention after loss of one zone.
- Regional loss has a documented and rehearsed recovery with a 15-minute RTO and a 5-minute RPO, subject to the measured replication-lag gate described below.
- The design is limited to managed services and an eight-engineer team.

## 2. GKE cluster and networking

- One regional GKE Standard cluster in europe-west2, with a replicated control plane and node pools distributed across all three zones.
- Use the Regular release channel (or Stable if required features support it), after compatibility testing. Define and test a maintenance window; upgrades must be rehearsed rather than assumed to be disruption-free.
- Separate system and application node pools, with cluster autoscaling and explicitly tested minimum/maximum node limits. Limits must cover peak load, loss of one zone, rolling upgrades, and surge capacity.
- Use VPC-native private nodes, restricted control-plane access, and regional Cloud NAT for internet egress.
- Size the pod secondary range from the calculated maximum pod count: maximum nodes × configured max-pods-per-node, plus system pods, rolling-upgrade surge, zone-loss capacity, and documented growth headroom. A /22 is insufficient; a /19 is an initial planning value only and must be confirmed by the capacity calculation before provisioning.
- Test IP exhaustion and scheduling behavior during autoscaling, zone failure, and upgrades.

## 3. Capacity and placement

- Baseline the API tier at least 13 replicas at the stated benchmark of 800 requests/second per pod. With `maxSkew: 1` across three zones, the worst distribution is 5/4/4; loss of the fullest zone leaves eight replicas, or 6,400 requests/second nominal capacity. Validate per-pod throughput under realistic load and retain additional tested headroom for rollout and failures; a higher or lower baseline requires equivalent measured justification.
- Provision each surviving zone/node pool to carry the full peak workload, including rollout headroom, without depending on rapid autoscaler reaction after a zone loss. Test the 13-replica baseline, surge capacity, and worst-case placement in a zone-failure game day.
- Spread replicas across zones with topology spread constraints (`maxSkew: 1`, `DoNotSchedule`).
- If one replica per node is required, use required hostname anti-affinity (or an equivalent enforced placement policy), not merely preferred anti-affinity. Validate that the policy remains schedulable during zone loss and upgrades.
- Use a PDB such as `minAvailable: 5` for the API tier, subject to capacity validation. Do not use a PDB equal to all replicas, since it can block voluntary disruption and upgrades.
- Use surge upgrades with tested `maxSurge` and `maxUnavailable` values, and verify serving capacity throughout drains and rollouts.

## 4. Traffic and regional failover

- Use a global external Application Load Balancer with health-checked backends in both regions and explicitly configured health-based regional failover. Merely having one backend per region is insufficient.
- Health checks must represent application readiness, not only process liveness; connection draining is configured and tested.
- The global load balancer redirects traffic during regional failure. It does not promote the database or update application configuration.
- Regional recovery therefore includes promoting the cross-region Cloud SQL replica, updating application database configuration/secrets, validating read/write behavior and data integrity, then enabling or confirming traffic to the recovered region.
- Rehearse the complete application and database sequence against the 15-minute RTO. Do not rely on a 3,600-second DNS TTL. If DNS is used for any part of cutover, use a validated low TTL and document resolver-caching limitations.

## 5. Cloud SQL and recovery

- Use Cloud SQL for PostgreSQL with regional HA for the primary and automatic same-region failover.
- The HA standby is not a read endpoint. Dashboards must use a supported read replica or separate reporting path; monitor its freshness, query impact, and failure behavior.
- Maintain an asynchronous cross-region read replica in europe-west1 for regional recovery. Monitor observed replication lag continuously and alert before five minutes. The documented RPO gate is measured lag of five minutes or less; if the gate is not met, the incident procedure records the potentially lost committed transactions and follows the approved recovery decision.
- The promotion runbook must cover replica promotion, application connection changes, write validation, consistency checks, and traffic cutover. Rehearse it at least annually.
- Remove unconditional restore-time claims. Define measured restore and validation targets by database size and test them with backups and point-in-time recovery. Document restore verification, application recovery, and the consequence if measured restore time exceeds the regional recovery objective.

## 6. CDC to BigQuery

- Datastream reads changes from the Cloud SQL primary using a supported logical-decoding configuration whose primary CPU, I/O, storage, and lock impact are load-tested and bounded.
- The monitored SLO is that every committed change reaches queryable BigQuery data within approximately five minutes, measured end-to-end at BigQuery rather than inferred only from source replication lag.
- Alert at three minutes of end-to-end freshness lag and define an operational response, including investigation of Datastream, destination, and BigQuery processing.
- Validate behavior at peak load, during database failover, and during regional recovery.
- Handle inserts, updates, and deletes correctly. Destination processing must be idempotent and safe under replay/duplicate delivery, with reconciliation procedures for gaps.
- The BigQuery staleness setting must not conflict with the five-minute freshness SLO; cost controls may be applied only after validating that required data remains queryable within the SLO.

## 7. Security

- Use Workload Identity Federation for GKE with one Google service account per tier and no exported keys.
- Deny cross-namespace traffic by default with NetworkPolicy.
- Enforce Binary Authorization for pipeline-built images.
- Protect personal-data columns with BigQuery policy tags and use customer-managed encryption keys.

## 8. Observability and testing

- Measure request success rate and latency at the load balancer and alert on one-hour and six-hour error-budget burn.
- Dashboard API capacity and scheduling, per-zone node headroom, autoscaler state, pod IP consumption, database HA/replica lag, restore-test results, Datastream lag, and end-to-end BigQuery freshness.
- Perform quarterly zone-failure and capacity game days, including the 13-replica placement, surviving-zone capacity, and rollout/surge scenario.
- Perform at least annual regional recovery rehearsals, including database promotion, application configuration, load-balancer failover, CDC behavior, and measured RTO/RPO results. Record findings and track remediation before build readiness is declared.