# Highly available GKE platform with a Cloud SQL analytics feed: design v3

Written by Agent I, the platform lead.

## 1. Targets

- Customer-facing service SLO: 99.95% monthly availability, measured as successful requests served within the agreed latency objective at the global load balancer. The resulting error budget is approximately 22 minutes per month.
- The design must account for the end-to-end dependency chain (load balancing, GKE, Cloud SQL, networking, and supporting services); individual component availability targets are not multiplied or assumed to produce the platform SLO.
- Survive the loss of one zone without human intervention.
- Survive loss of the primary region through a documented and rehearsed recovery in a second region, with an RTO of 15 minutes and an RPO of 5 minutes, subject to measured replication lag.
- Peak traffic is approximately 5,000 requests per second. The team consists of eight engineers operating managed services.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled.
- The pod secondary range is sized substantially above immediate need—for example, a /19 range with 8,192 addresses—and is validated against the maximum node count, pod density, upgrade surge, and autoscaling headroom before production.
- The cluster is VPC-native with private nodes. Access to the control-plane endpoint is limited to authorised networks. Egress to the internet uses Cloud NAT on a regional Cloud Router.
- The cluster uses the Stable GKE release channel. Version upgrades are tested in a non-production cluster and rolled out through a documented maintenance process. A weekly maintenance window runs on Sunday from 02:00 to 06:00 local time.

## 3. Capacity

- Each API pod is expected to serve approximately 800 requests per second. Eight replicas provide baseline capacity above the 5,000-request-per-second peak, with load testing validating this assumption and the selected CPU, memory, latency limits, burst headroom, and capacity after loss of one zone.
- Each zone's node pool is sized for approximately 60% utilisation at peak traffic. After loss of one zone, the remaining zones carry the traffic at approximately 90% utilisation while the autoscaler adds capacity.
- Cluster autoscaler minimums and maximums are explicitly configured for each node pool. Scale-up capacity, scheduling time, and post-zone-loss recovery are measured in load and failure tests; the measured scale-up latency and tested degraded-zone capacity are recorded in the capacity plan and used for alerting and operational decisions.
- Capacity plans include system pods, rolling-upgrade surge nodes, daemonsets, failure headroom, and the larger pod range.

## 4. Workload placement and disruption

- Stateless tiers run eight replicas, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Preferred pod anti-affinity on the hostname key reduces co-location of replicas; topology spreading is the primary zone-level guarantee.
- Each tier has a PodDisruptionBudget with `minAvailable: 5` of 8. This permits controlled voluntary disruption while retaining serving capacity. Application readiness probes and graceful termination are required.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to capacity and disruption-budget checks.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use the application's `/healthz` endpoint, and connection draining is 60 seconds.
- Regional failover uses the load balancer's health-based backend failover and routing, not DNS-only failover. The procedure includes validating health-check behaviour, capacity, and application readiness in the secondary region.
- DNS is not relied upon for the 15-minute failover bound. Any DNS records used operationally have a bounded, documented TTL, and client/resolver caching limitations are included in the RTO test.

## 6. Database

- The transactional database is Cloud SQL for PostgreSQL in europe-west2 with high availability enabled: a primary in one zone and a standby in another, with automatic intra-region failover. Automated backups and point-in-time recovery are enabled.
- The HA standby is not used for queries. Dashboards use a separately provisioned Cloud SQL read replica (or an equivalent explicitly provisioned reporting path), sized and monitored for analytics workload. Its lag and availability are separate operational metrics and SLOs.
- A cross-region read replica in europe-west1 is the regional-recovery target and is promoted by a documented runbook. The 5-minute regional RPO is validated from measured replica lag, with alerts and escalation when lag approaches the limit.
- Backup restoration time is not assumed to be independent of database size. Restore and point-in-time-recovery duration, data validation, and cutover are measured in rehearsal and documented as part of the recovery procedure. A bad migration is handled using the tested recovery procedure.

## 7. Change data capture to BigQuery

- Datastream reads changes from the Cloud SQL primary using a supported PostgreSQL logical-decoding configuration and writes them to BigQuery. The configuration is tested to ensure replication slots, WAL retention, CPU, storage, and network usage do not endanger primary performance.
- The CDC freshness target is five minutes, with alerts at three minutes. Replication-slot health, WAL retention, Datastream errors, throughput, and lag are monitored.
- The BigQuery destination's staleness limit is 15 minutes for cost control, but this does not replace the five-minute CDC freshness objective.
- Change events are applied idempotently, using a merge on the primary key and an event/version ordering strategy appropriate to the source schema, so retries do not create duplicate rows.
- CDC freshness and Cloud SQL cross-region replication lag are separate SLOs and are included in recovery testing.

## 8. Security

- Workloads reach Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default, and Binary Authorization admits only images built by the approved pipeline.
- Columns holding personal data are covered by policy tags in BigQuery, and datasets use customer-managed encryption keys.

## 9. Observability

- Service-level indicators are request success rate and latency measured at the load balancer. Alerts cover one-hour and six-hour error-budget burn rates.
- Dashboards show regional backend health, failover state, Cloud SQL HA and read-replica lag, cross-region replica lag, CDC freshness, replication-slot/WAL status, node-pool capacity per zone, pod scheduling, and autoscaler state.
- Alerts have documented owners, runbooks, and escalation paths.

## 10. Testing and operations

- A zone-failure game day is conducted every quarter.
- A full regional recovery rehearsal is conducted at least annually and includes load-balancer failover, cross-region database promotion, application validation, CDC behaviour, measured RTO/RPO, and rollback or failback planning.
- Backup restoration and point-in-time recovery are tested at a frequency appropriate to the database recovery requirements.
- Load and zone-failure tests measure API capacity, burst and degraded-zone headroom, autoscaler maximums, and post-zone-loss scale-up latency.
- Each exercise produces a written report with measured results, gaps, owners, and due dates.