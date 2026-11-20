# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets

- End-to-end service availability SLO: 99.95% per month, measured as successful, correctly served customer requests divided by eligible requests at the load balancer (approximately 22 minutes of monthly error budget).
- This is not derived by multiplying component availability claims. GKE, Cloud SQL, load balancing, networking, CDC, and dependencies have tracked operational objectives and explicit attribution in error-budget reviews.
- Survive loss of one zone without human intervention.
- Recover from loss of the whole region in a second region with a rehearsed RTO of 15 minutes and RPO of 5 minutes.
- Peak traffic is approximately 5,000 requests per second. The team consists of eight engineers operating managed services.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across three zones and node pools in all three zones.
- Separate system and application node pools, each with cluster autoscaling enabled.
- The pod secondary range is sized from the maximum autoscaler node count, GKE per-node pod allocation, upgrade surge nodes, and growth headroom. Capacity calculation and a pre-build allocation test must demonstrate that the selected range supports all of these; `/19` is the initial allocation unless the calculation justifies another size.
- The cluster is VPC-native with private nodes. Control-plane access is limited to authorised networks. Internet egress uses Cloud NAT through a regional Cloud Router.
- Production uses the Regular GKE release channel. Releases and maintenance are tested and scheduled during a weekly Sunday 02:00–06:00 local-time window.

## 3. Capacity

- Each API pod serves approximately 800 requests per second; six replicas therefore exceed the 5,000-request-per-second peak.
- Each zone is sized for approximately 60% utilisation at peak. After losing one zone, the remaining zones carry the same traffic at approximately 90%, with autoscaling adding capacity.
- Capacity tests cover zone loss, rolling upgrades, autoscaler delay, and configured surge capacity. Node maximums and secondary-range sizing are revised if tests require more headroom.

## 4. Workload placement and disruption

- Stateless tiers run six replicas across zones with topology spread constraints (`maxSkew: 1`, `whenUnsatisfiable: DoNotSchedule`).
- Preferred hostname anti-affinity encourages replicas onto separate nodes.
- Each tier has a PodDisruptionBudget with `minAvailable: 5`, allowing one voluntary disruption while retaining service capacity.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`. Upgrade and drain behavior is validated with the available spare capacity.

## 5. Traffic and regional recovery

- Traffic enters through a global external Application Load Balancer with a backend in each region. Health checks use `/healthz`; connection draining is 60 seconds.
- Regional failover uses the load balancer’s documented health-based backend failover mechanism. Recovery rehearsals test health checks, draining, application startup, database promotion, application configuration, and client behavior.
- DNS and client caching are not the primary failover mechanism. Any DNS records have a TTL and operational process compatible with the 15-minute RTO, and resolver/cache behavior is verified.

## 6. Database

- Cloud SQL for PostgreSQL runs in europe-west2 with HA enabled: a primary in one zone and a standby in another, with automatic in-region failover. Automated backups and point-in-time recovery are enabled.
- Analytics uses a separately provisioned, supported Cloud SQL read replica, not the HA standby. Its capacity, replication lag, and dashboard freshness are monitored and documented.
- A cross-region read replica in europe-west1 is promoted by a documented regional-recovery runbook. Replica lag is continuously monitored; alerts fire before five minutes, and promotion/data-loss expectations are recorded. Recovery rehearsals must demonstrate the five-minute RPO.
- Restore and point-in-time recovery duration is measured using representative database sizes and exercised in drills. If measured restoration does not support the 15-minute RTO, capacity, procedures, or objectives are revised.

## 7. Change data capture to BigQuery

- Datastream reads Cloud SQL logical-decoding changes and writes to BigQuery. Target freshness is five minutes; an alert fires at three minutes.
- Replication slots, WAL retention, CDC resource usage, and primary storage are monitored. The initial operational thresholds are:
  - warning at 70% of the configured WAL-retention or primary-storage budget;
  - urgent alert and operator action at 85%;
  - a hard protection threshold before exhaustion, with the exact value validated in load tests and documented in the runbook.
- Alerts identify the owner and require reducing or stopping CDC intake, correcting the consumer, and preventing unbounded WAL growth. Datastream is throttled or paused when lag or WAL/storage pressure threatens primary transaction health; it is resumed only after the runbook’s checks pass. CDC must never be allowed to exhaust primary storage or materially degrade transaction latency.
- BigQuery’s data-staleness limit is 15 minutes to control query costs. Change events use a primary-key merge so duplicate events do not create duplicate rows.
- CDC freshness, completeness, slot/WAL thresholds, backpressure, and restart recovery are tested during failure exercises.

## 8. Security

- Workloads access Google Cloud APIs through Workload Identity Federation for GKE, with one Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only pipeline-built images.
- Personal-data columns use BigQuery policy tags, and datasets use customer-managed encryption keys.

## 9. Observability

- SLIs are load-balancer request success rate and latency. Alerts use one-hour and six-hour error-budget burn rates.
- Dashboards show analytics and cross-region replica lag, CDC freshness, slot/WAL retention, primary-storage pressure, node capacity per zone, autoscaler state, backend health, and regional failover status.
- Alerts have documented ownership and response procedures. Dependency failures are included in end-to-end error-budget reviews.

## 10. Validation and testing

Before production build approval, the team must:

- capacity-test the selected pod secondary range using maximum autoscaler nodes, upgrade surge, and growth headroom;
- test zone loss, upgrades, PDB behavior, and autoscaler delay;
- rehearse regional recovery, including load-balancer failover, Cloud SQL promotion, application configuration, and client behavior, demonstrating measured RTO ≤15 minutes and RPO ≤5 minutes;
- test backup restoration and point-in-time recovery against representative database sizes;
- test Datastream lag, replication-slot/WAL-retention thresholds, primary-storage alerts, backpressure, pause/resume behavior, and recovery without harming transaction latency.

A zone-failure game day occurs quarterly. A full regional recovery rehearsal occurs annually with a written report covering measured RTO, RPO, replica lag, restoration duration where applicable, failover behavior, and DNS/client behavior. Controls are retested after material changes.