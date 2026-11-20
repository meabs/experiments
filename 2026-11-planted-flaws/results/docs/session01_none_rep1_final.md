# Highly available GKE platform with a Cloud SQL analytics feed: design v2

## 1. Targets and SLO

- The customer-facing platform has a measured end-to-end monthly availability SLO of 99.95% (about 22 minutes of monthly error budget), with explicit error-budget allocation across load balancing, GKE, Cloud SQL, networking, and dependencies. Component targets are not assumed to compose to 99.95%.
- The platform must survive loss of one zone without operator action.
- Regional loss is recovered through a documented and rehearsed procedure with an RTO of 15 minutes and an RPO of 5 minutes. These objectives include traffic routing, database promotion, application connection cutover, and CDC recovery.
- Peak traffic is approximately 5,000 requests/second. The team is eight engineers using managed services.

## 2. Cluster and node topology

- Use one regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools in all three zones.
- Use separate system and application node pools, each with cluster autoscaling. Define tested minimum and maximum node counts, quotas, and spare capacity sufficient to recover from a zone loss and accommodate upgrade surge.
- Use VPC-native private nodes. Size the pod secondary range for the maximum node count, GKE per-node pod allocation, upgrade surge, autoscaling, and growth; `/18` is an initial estimate to validate, with reserved expansion capacity.
- Limit control-plane access to authorised networks. Use Cloud NAT for internet egress.
- Use the Regular GKE release channel (or Stable if compatible with required features), with a tested maintenance window and upgrade/rollback procedure.

## 3. Capacity

- Each API pod serves approximately 800 requests/second. Run at least six replicas and validate capacity, resource requests/limits, and autoscaler behavior through load testing.
- Size each zone for post-zone-loss traffic and validate that remaining capacity and autoscaler quotas meet the target without relying on unverified 90% utilisation assumptions.

## 4. Workload placement and disruption

- Run six replicas of stateless tiers with topology spread constraints across zones.
- Use required hostname anti-affinity when one replica per node is a hard requirement; otherwise validate placement and document the exception.
- Set a disruption budget such as `minAvailable: 5` of 6, preserving tested serving capacity while permitting voluntary drains and upgrades.
- Use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to sufficient pod IPs, quota, and spare nodes.

## 5. Traffic and regional recovery

- Use a global external Application Load Balancer with healthy backends in both regions and tested health-based regional failover. DNS is not the primary failover mechanism; if DNS is used, use a bounded TTL and document resolver-cache limitations.
- Health checks must represent application readiness, including database/write readiness where appropriate. Connection draining is 60 seconds and must be tested.
- The regional recovery runbook must: stop or fence writes in the failed region as applicable, promote the cross-region Cloud SQL replica, update application connection configuration and write readiness, route traffic to the recovery region, and verify service health.
- Rehearse the complete procedure and record measured RTO and RPO.

## 6. Database

- Use Cloud SQL for PostgreSQL HA in europe-west2, with automated backups and point-in-time recovery enabled.
- The HA standby is not a read endpoint. Dashboards use a separately provisioned supported read replica or another explicitly supported analytics path, with capacity, lag, and failure behavior monitored.
- Maintain a cross-region read replica in europe-west1 for regional recovery. Alert on replica lag and verify in rehearsals that measured lag meets the 5-minute RPO; do not claim a size-independent restore time.
- Define and test backup restore times by database size. The cross-region replica promotion path is the normal regional recovery path; backup restore is a separately measured fallback.

## 7. Change data capture to BigQuery

- Configure Datastream from Cloud SQL logical decoding to BigQuery with documented prerequisites.
- Protect the primary by monitoring replication-slot retention and WAL growth, Datastream lag, source load, and backpressure; define throttling/pausing and remediation procedures.
- Measure freshness at the BigQuery data used by consumers. Alert on CDC lag/freshness independently from cross-region database replica lag.
- Apply events idempotently (for example, merge by primary key), and document restart, replay, deduplication, and reconciliation after regional recovery. Validate that CDC does not endanger the primary.

## 8. Security

- Use Workload Identity Federation for GKE, one Google service account per tier, and no exported keys.
- Deny cross-namespace traffic by default with network policies. Use Binary Authorization for pipeline-built images.
- Apply BigQuery policy tags to personal data and use customer-managed encryption keys.

## 9. Observability

- Measure request success rate and latency at the load balancer and define the end-to-end SLO and burn-rate alerts.
- Dashboard zonal node/pod capacity, autoscaler state and limits, quotas, database health, read-replica and cross-region replica lag, Datastream freshness, slot/WAL growth, and BigQuery freshness.
- Alert before capacity, lag, or WAL retention threatens the availability, RPO, or CDC objectives.

## 10. Testing and operations

- Conduct quarterly zone-failure game days and at least annual full regional recovery rehearsals.
- Test upgrades, pod placement, autoscaling, load-balancer failover, database promotion, application connection cutover, CDC restart/reconciliation, backup restore, and observability.
- Retain written reports with measured availability, RTO, RPO, restore times, replica lag, CDC freshness, and corrective actions.

AGREE v2