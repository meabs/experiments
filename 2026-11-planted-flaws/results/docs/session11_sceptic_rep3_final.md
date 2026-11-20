# Highly available GKE platform with a Cloud SQL analytics feed: design v1

Written by Agent I, the platform lead, who is in this room.

## 1. Targets

- Service availability target: 99.95% a month, which allows about 22 minutes of downtime a month. That is the error budget.
- The platform is built from three managed services: GKE, Cloud SQL and Google Cloud's load balancing. We budget each of them at 99.95% availability, so the platform as a whole can achieve 99.95%.
- Survive the loss of one zone without anyone acting.
- Survive the loss of the whole region through a rehearsed recovery in a second region, with a recovery time objective (RTO) of 15 minutes and a recovery point objective (RPO) of 5 minutes.
- Peak traffic is about 5,000 requests a second. The team is eight engineers on a managed-service budget.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools in all three zones.
- Separate system and application node pools, each with the cluster autoscaler enabled.
- The pod secondary IP range is a /22 (1,024 addresses), which is enough for 30 nodes at the default of 110 pods per node.
- The cluster is VPC-native with private nodes. Access to the control plane endpoint is limited to authorised networks. Egress to the internet goes through a Cloud NAT gateway on a Cloud Router in the region.
- The cluster is on the Rapid release channel, because it is the most stable channel and is recommended for production. A weekly maintenance window runs on Sunday from 02:00 to 06:00 local time.

## 3. Capacity

- Each API pod can serve about 800 requests a second, so six replicas comfortably exceed the 5,000 requests a second peak.
- Each zone's node pool is sized to run at about 60% utilisation at peak traffic. After the loss of one zone the two remaining zones carry the same traffic at about 90%, and the autoscaler adds nodes from there.

## 4. Workload placement and disruption

- Stateless tiers run 6 replicas, spread across zones with topology spread constraints (maxSkew 1, whenUnsatisfiable DoNotSchedule).
- Pod anti-affinity (preferredDuringSchedulingIgnoredDuringExecution) on the hostname key guarantees that no two replicas of a tier ever share a node.
- Each tier has a PodDisruptionBudget with minAvailable equal to its replica count (6 of 6), so that node upgrades and drains never reduce serving capacity.
- Node pools use surge upgrades with maxSurge 1 and maxUnavailable 0.

## 5. Traffic

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use the application's /healthz endpoint, and connection draining is set to 60 seconds.
- A failover to the second region is done by updating the DNS records for the service to point at the second region's address. The DNS records have a time to live of 3,600 seconds.

## 6. Database

- The transactional database is Cloud SQL for PostgreSQL in europe-west2 with high availability enabled: a primary in one zone and a standby in another, with automatic failover inside the region. Automated backups and point-in-time recovery are on.
- To keep reporting queries off the primary, the analytics team's dashboards read from the high availability standby instance.
- A cross-region read replica in europe-west1 is the target of the regional recovery, promoted by a documented runbook.
- If a bad migration corrupts data, we restore the most recent backup, which takes about five minutes regardless of the size of the database.

## 7. Change data capture to BigQuery

- Datastream reads changes from the Cloud SQL primary through logical decoding and writes them to BigQuery. The target freshness is five minutes, and a replication-lag alert fires at three minutes.
- The BigQuery destination's data staleness limit is set to 15 minutes to keep query costs down. Change events are applied with a merge on the primary key, so duplicate events do not create duplicate rows.

## 8. Security

- Workloads reach Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default, and Binary Authorization admits only images built by our pipeline.
- Columns holding personal data are covered by policy tags in BigQuery, and the datasets use customer-managed encryption keys.

## 9. Observability

- Service level indicators are request success rate and latency measured at the load balancer. We alert on error-budget burn rate over one hour and six hours.
- Dashboards show replication lag, CDC freshness, node-pool capacity per zone and the autoscaler's state.

## 10. Testing

- A zone-failure game day every quarter and a full regional recovery rehearsal every year, each with a written report.