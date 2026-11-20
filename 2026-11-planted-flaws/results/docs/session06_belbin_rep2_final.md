# Highly available GKE platform with Cloud SQL analytics feed — design v3

## 1. Targets and SLO

- End-to-end monthly availability SLO is 99.95% for successful, latency-compliant customer requests, measured at the global load balancer. Component objectives are subordinate to this SLO; their availability is not multiplied as if it were an end-to-end guarantee.
- The platform must tolerate loss of one zone without operator intervention and remain below the tested safe utilization ceiling.
- Regional recovery is rehearsed with a target RTO of 15 minutes and RPO of 5 minutes, subject to measured asynchronous-replication lag. These targets are not considered achieved until acceptance tests pass.
- Peak traffic is approximately 5,000 requests per second.

## 2. GKE topology

- Use one regional GKE Standard cluster in europe-west2, with nodes distributed across all three zones.
- Use separate system and application node pools, both with cluster autoscaling. Use the Regular release channel (or Stable if all required features are supported), with a tested maintenance window and upgrade procedure.
- Use VPC-native private nodes, authorized control-plane networks, and regional Cloud NAT.
- Size the pod secondary range to at least /19, based on actual GKE per-node CIDR allocation, maximum node count, upgrade surge, and growth. Document expansion capacity and alerting. Validate IP and node capacity during scale and zone-failure tests.

## 3. Capacity and placement

- Six API replicas exceed the 5,000-request/second peak based on current load testing. Capacity assumptions will be revalidated in load tests.
- Maintain sufficient pre-provisioned spare capacity so loss of one zone does not exceed the tested safe utilization ceiling or require autoscaler recovery to serve normal peak traffic.
- Use required topology spread constraints across zones and required hostname anti-affinity where one replica per node is necessary.
- Use a PodDisruptionBudget such as `minAvailable: 5` for six replicas, subject to maintenance testing. Node-pool upgrades use surge capacity and `maxUnavailable: 0`; upgrades must be tested to confirm they do not violate the availability SLO.

## 4. Warm standby and regional recovery

- Maintain a provisioned warm-standby GKE cluster in europe-west1 with pre-provisioned minimum capacity sufficient to serve the validated 5,000-request/second workload without pending pods or dependence on autoscaler reaction. It has documented node pools, pod-IP headroom, networking, regional NAT, IAM/KMS access, and autoscaler limits.
- Continuously synchronize and drift-check images, manifests, configuration, secrets, IAM/KMS permissions, networking, and capacity. Alert on divergence and perform a pre-failover readiness test during each regional rehearsal.
- Register the standby as a backend of a global external Application Load Balancer, but gate readiness so it remains out of service or read-only until database promotion, endpoint/configuration changes, integrity checks, and write validation succeed.
- Use health-based regional failover; do not rely on a 3,600-second DNS TTL. Health checks represent application and database readiness, and connection draining is 60 seconds.
- Recovery sequence is: detect failure and converge traffic policy; fence writes in the old region; verify replica lag and the five-minute RPO objective; promote the cross-region database replica; update connection endpoints, configuration, and secrets; run integrity checks; validate transactional writes; then enable write traffic. The runbook prevents split-brain and records timings for every step.
- The regional rehearsal must demonstrate that detection/LB convergence, fencing, lag validation and promotion, configuration updates, integrity checks, and write validation together fit within 15 minutes. If safe write recovery cannot fit, serve an explicitly documented read-only/degraded mode rather than accepting unsafe writes.
- The regional recovery runbook includes rollback, and records measured standby readiness, failover capacity, promotion, and application recovery times.

## 5. Cloud SQL

- Cloud SQL for PostgreSQL uses regional HA with automatic zonal failover.
- The HA standby is not used for reads. Analytics dashboards use a separately provisioned, supported read replica, sized and monitored for query load and replication lag.
- A cross-region read replica in europe-west1 is the regional-recovery target. Replication is asynchronous; the five-minute RPO is an objective verified by measured lag, not an assumption.
- Backups and point-in-time recovery are enabled. Restore duration is stated only after testing at representative database sizes; the runbook records measured restore RTO/RPO rather than asserting a universal five-minute restore.

## 6. CDC to BigQuery

- Datastream uses a supported Cloud SQL PostgreSQL logical-decoding configuration, validated in a production-like test without unacceptable primary impact.
- The target freshness objective is five minutes, with alerting before that objective is breached.
- Monitor replication lag, slot/WAL retention, source CPU/IO, and Datastream errors. Define bounded retention and an operational response for prolonged outages or backpressure so primary storage cannot fill.
- During CDC interruption, changes are retained/replayed where supported and the pipeline is reconciled from a recorded checkpoint; duplicates are handled idempotently. BigQuery staleness settings do not substitute for CDC freshness monitoring.
- CDC freshness and reconciliation are acceptance-tested during regional recovery and representative load.

## 7. Security, observability and testing

- Use Workload Identity Federation for GKE, one Google service account per tier, default-deny namespace network policies, Binary Authorization, BigQuery policy tags, and customer-managed encryption keys.
- Monitor request success/latency, error-budget burn, regional health, database failover and replica lag, CDC freshness/WAL retention, node capacity by zone, autoscaler state, standby drift, and readiness gating.
- Perform quarterly zone-failure and maintenance game days. Perform at least annual regional recovery, database promotion/restore, and CDC reconciliation rehearsals. Record measured LB convergence, fencing, promotion, endpoint/configuration updates, integrity checks, write validation, restore times, replication lag, CDC freshness, standby capacity, and corrective actions before treating the objectives as achieved.