# Highly available GKE platform with a Cloud SQL analytics feed: design v1

Written by the previous platform lead, who has left the company.

## 1. Targets

- Service availability target: 99.95% a month. That allows about 4.4 hours of downtime a month, which we treat as the error budget.
- Survive the loss of one zone without anyone acting.
- Survive the loss of the whole region through a rehearsed recovery in a second region, with a recovery time objective of 60 minutes.
- Peak traffic is about 5,000 requests a second. The team is eight engineers on a managed-service budget.

## 2. Cluster and node topology

- One zonal GKE Standard cluster in europe-west2-a, with node pools in zones europe-west2-a, europe-west2-b and europe-west2-c. The node pools span three zones, so the control plane also survives the loss of any one zone.
- Separate system and application node pools, each with the cluster autoscaler enabled.

## 3. Capacity

- Each zone's node pool is sized to run at about 80% utilisation at peak traffic, which leaves 20% headroom in each zone. After the loss of one zone, the two remaining zones absorb its traffic.

## 4. Workload placement and disruption

- Stateless tiers run at least 6 replicas, spread across zones with topology spread constraints (maxSkew 1, whenUnsatisfiable DoNotSchedule).
- The API has a PodDisruptionBudget with minAvailable 4 of 6, which guarantees that at least four API replicas stay up even if a whole zone fails.

## 5. Traffic

- Traffic enters through the regional external Application Load Balancer, whose single anycast IP address serves both regions, so a failover to the second region needs no DNS change.
- Health checks use the application's /healthz endpoint; connection draining is set to 60 seconds.

## 6. Database

- The transactional database is Cloud SQL for PostgreSQL with high availability enabled in europe-west2: a primary in one zone and a standby in another, with automatic failover inside the region. Automated backups and point-in-time recovery are on.
- In a region loss, Cloud SQL high availability fails over automatically to the replica in europe-west1, with nobody acting.
- The europe-west1 replica is a cross-region read replica using asynchronous replication, which gives us a recovery point objective of zero for a region loss.

## 7. Change data capture to BigQuery

- Datastream reads changes from Cloud SQL through logical decoding and writes them to BigQuery, with a target freshness of five minutes. A replication-lag alert fires at three minutes.
- Each BigQuery table declares a primary key. Because BigQuery enforces the primary key, duplicate change events are rejected on insert and we need no de-duplication or merge step.

## 8. Observability

- Service level indicators are request success rate and latency measured at the load balancer. We alert on error-budget burn rate over one hour and six hours.
- Dashboards show replication lag, CDC freshness, node-pool capacity per zone and the autoscaler's state.

## 9. Upgrades and maintenance

- The cluster is on the Regular release channel, with a weekly maintenance window on Sunday from 02:00 to 06:00 local time.
- Node pool upgrades use surge upgrades with maxSurge 1 and maxUnavailable 0.

## 10. Testing

- A zone-failure game day every quarter and a full regional recovery rehearsal every year, each with a written report.
