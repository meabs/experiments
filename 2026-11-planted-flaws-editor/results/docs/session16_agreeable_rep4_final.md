# Highly available GKE platform with a Cloud SQL analytics feed: design v2

## 1. Targets and availability

- Service availability SLO: 99.95% per month, with an error budget of approximately 22 minutes.
- The SLO is an end-to-end target measured at the load balancer. It is not derived by assuming that component availabilities can be multiplied or that three 99.95% services automatically provide 99.95% platform availability.
- Availability budgets include GKE, Cloud SQL, load balancing, networking, dependencies, maintenance, and regional-failover behavior. These dependencies and the associated alerting and error-budget policy will be documented before production.
- The platform must survive loss of one zone without operator intervention.
- Loss of the whole region must be recoverable through a documented, rehearsed procedure in a second region, with RTO 15 minutes and RPO 5 minutes.
- Peak traffic is approximately 5,000 requests per second. The team consists of eight engineers operating managed services.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across the region's three zones and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled.
- The pod secondary IP range will be sized for the maximum planned node count, 110 pods per node, and growth/headroom. It will not be a /22; an initial /19 (or an equivalently sized range justified by the final node envelope) will be provisioned, with expansion planning documented.
- The cluster is VPC-native with private nodes. Access to the control-plane endpoint is limited to authorised networks.
- Internet egress uses Cloud NAT on a regional Cloud Router.
- Use the Regular GKE release channel (Stable may be selected if it meets required features and support policy), not Rapid. Upgrades will be validated before rollout and performed in the Sunday 02:00–06:00 local-time maintenance window.

## 3. Capacity

- Each API pod serves approximately 800 requests per second; six replicas therefore exceed the 5,000 requests-per-second peak with headroom.
- Node pools are sized so each zone runs at approximately 60% utilisation at peak traffic. After loss of one zone, the remaining zones carry the traffic at approximately 90% until autoscaling adds capacity.
- The node, IP-range, quota, and autoscaler limits will be tested against peak load, zone loss, and the planned growth envelope.

## 4. Workload placement and disruption

- Stateless tiers run six replicas, spread across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Preferred pod anti-affinity on the hostname key reduces replica co-location; capacity and scheduling tests will verify the resulting placement.
- Each tier has a PodDisruptionBudget with `minAvailable: 5`. This permits controlled voluntary disruption while retaining availability during a single eviction; zonal resilience is provided by spreading and spare/autoscaled capacity.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region.
- Health checks use the application's `/healthz` endpoint, and connection draining is 60 seconds.
- Regional failover uses the load balancer's health-based regional failover/routing. It does not depend on a 3,600-second DNS TTL.
- Any DNS used for service naming will have a TTL compatible with the 15-minute RTO, and resolver/cache limitations will be documented and tested.
- Regional recovery includes promotion of the Cloud SQL cross-region replica, switching the write endpoint, bringing up or scaling the secondary-region GKE workload, and validating application and data health.

## 6. Database

- The transactional database is Cloud SQL for PostgreSQL in europe-west2 with high availability enabled: a primary in one zone and a standby in another, with automatic in-region failover. Automated backups and point-in-time recovery are enabled.
- The HA standby is not used as a read endpoint. Analytics dashboards use a separately configured and suitably sized supported read replica, with replica lag, capacity, and failure behavior monitored and documented.
- A cross-region read replica in europe-west1 is the regional-recovery target. Its replication lag is monitored and must meet the 5-minute RPO requirement before the system is considered ready for production.
- Promotion and application write-endpoint changes are defined in a documented runbook and tested during regional recovery rehearsals.
- Restore time is database-size- and workload-dependent; no fixed five-minute guarantee is assumed. Restore procedures have a tested, documented recovery objective, and results are included in recovery planning.

## 7. Change data capture to BigQuery

- Datastream reads changes from the Cloud SQL primary through logical decoding and writes them to BigQuery without placing reporting load on the primary.
- The target freshness is five minutes, with an alert at three minutes. Replication slots, source impact, storage growth, and lag are monitored.
- The BigQuery destination's data-staleness limit is 15 minutes to control query costs.
- Change events are merged on the primary key, so duplicate delivery does not create duplicate rows.
- CDC behavior and recovery are tested to confirm that committed changes reach BigQuery within the required approximately five-minute target without endangering the primary.

## 8. Security

- Workloads reach Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny traffic between namespaces by default, and Binary Authorization admits only images built by the approved pipeline.
- Columns containing personal data are covered by policy tags in BigQuery, and datasets use customer-managed encryption keys.

## 9. Observability

- Service-level indicators are request success rate and latency measured at the load balancer. Alerts cover one-hour and six-hour error-budget burn rates.
- Dashboards show Cloud SQL HA and read-replica status, cross-region replication lag, CDC freshness and lag, node-pool capacity per zone, autoscaler state, load-balancer health, and regional-failover readiness.
- Alerts and runbooks cover replica lag exceeding the RPO threshold, CDC lag exceeding its target, failed health checks, exhausted IP or node capacity, and failed failover prerequisites.

## 10. Testing and operational readiness

- A zone-failure game day is conducted every quarter.
- A full regional recovery rehearsal is conducted at least annually and verifies the 15-minute RTO, 5-minute RPO, load-balancer failover, database promotion, endpoint switching, and workload capacity.
- Restore testing is performed using representative database sizes and records measured recovery times.
- Each exercise produces a written report with findings, corrective actions, owners, and due dates.