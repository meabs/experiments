# Highly available GKE platform with a Cloud SQL analytics feed: design v3

## 1. Targets and availability budget

- Customer-facing stateless web/API service SLO: 99.95% monthly availability, measured at the global load balancer. The 22-minute monthly error budget covers application and platform failures; dependency budgets and failover actions are tracked separately.
- Survive loss of one zone automatically.
- Survive regional loss through a documented, rehearsed recovery in europe-west1, with a 15-minute RTO and 5-minute RPO, subject to the measured database replication objective.
- Peak traffic is about 5,000 requests/second. The team is eight engineers using managed services.

## 2. Cluster and node topology

- One regional GKE Standard cluster in europe-west2, with the control plane replicated across three zones and node pools distributed across all three zones.
- Separate system and application node pools, each with cluster autoscaling. Capacity, quotas, and scale-up time are tested for loss of a zone; sufficient spare capacity is pre-provisioned so the remaining zones can serve peak traffic without relying solely on reactive scale-up.
- Use a VPC-native cluster with a pod secondary range sized for at least 30 nodes at 110 pods/node plus surge and growth headroom (not /22); reserve and document expansion capacity.
- Private nodes and authorised control-plane networks. Internet egress uses Cloud NAT with regional quota and failure monitoring.
- Use the Regular GKE release channel (Stable if it meets required feature needs), with a tested upgrade policy and a weekly maintenance window Sunday 02:00–06:00 local time.

## 3. Capacity and placement

- Run a tested baseline of at least nine API replicas. Capacity testing must demonstrate at least 900 requests/second per pod at the required latency SLO, so the six replicas remaining in the two surviving zones after the worst expected zone placement provide at least 5,400 requests/second. Validate additional rollout, failure, and traffic-growth headroom; increase the baseline if testing does not meet these criteria.
- Stateless tiers use topology spread constraints across zones with `maxSkew: 1` and `DoNotSchedule`. Use required hostname anti-affinity where node separation is required.
- Set PDBs to permit controlled voluntary disruption, initially `minAvailable: 5` for the nine-replica baseline, and validate this against capacity and upgrade tests. Do not use a PDB that can block drains indefinitely.
- Node pools use surge upgrades with `maxSurge: 1` and `maxUnavailable: 0`, subject to sufficient spare quota and IP capacity.

## 4. Traffic and regional recovery

- Use a global external Application Load Balancer with regional backends, health checks on a dependency-appropriate `/healthz`, and 60-second connection draining.
- Configure health-based regional failover at the load-balancer layer. Do not depend on a 3,600-second DNS TTL for the 15-minute RTO. Any DNS used for recovery has a controlled low TTL, and resolver/client caching limitations are documented.
- The regional recovery runbook covers declaring the incident, fencing the failed region and preventing writes there, confirming replica lag and promotion eligibility, promoting the database replica, updating the application’s database endpoint/secrets and reconnecting clients, selecting the recovered application backend, validating health and writes, and directing traffic. Rehearse it annually and measure the complete RTO.

## 5. Database

- Cloud SQL for PostgreSQL HA is primary protection: primary and standby are in separate zones with automatic regional failover.
- The HA standby is not used for analytics. Dashboards use a separate, appropriately sized Cloud SQL read replica (or another explicitly approved replicated analytics target), with lag, capacity, and availability monitoring.
- Maintain a cross-region read replica in europe-west1. Define and alert on replication lag, verify that it stays within the 5-minute RPO objective, and test promotion and application connection changes during every regional rehearsal.
- Automated backups and point-in-time recovery are enabled. Restore RTO is measured through regular size-representative restore tests; no fixed “five minutes regardless of database size” guarantee is assumed. Document the tested restore RTO/RPO separately from replica promotion.

## 6. Change data capture to BigQuery

- Datastream reads Cloud SQL changes using a supported logical-decoding configuration and writes to BigQuery. Configure and monitor replication slots and WAL retention so CDC cannot exhaust primary storage or otherwise endanger the primary.
- Target freshness is five minutes, with alerts early enough to leave margin (for example at two minutes, with escalation before five minutes). Monitor primary CPU, I/O, storage, WAL and slot lag.
- BigQuery staleness limit is 15 minutes. Merge/upsert processing is idempotent so duplicate events do not create duplicate rows.

## 7. Security, observability and testing

- Workloads use Workload Identity Federation for GKE, one Google service account per tier, with no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only pipeline-built images.
- BigQuery personal-data columns use policy tags and datasets use customer-managed encryption keys.
- SLIs are load-balancer request success rate and latency. Dashboards include database/read-replica/cross-region lag, CDC freshness and slot/WAL health, node capacity by zone, quotas, autoscaler state, and failover readiness. Alert on one-hour and six-hour error-budget burn.
- Run a zone-failure game day quarterly, database restore and promotion tests regularly, and a full regional recovery rehearsal annually; retain written results and update measured RTO/RPO and capacity assumptions. Acceptance requires surviving-zone capacity above 5,000 requests/second, including rollout and failure headroom, and regional recovery within 15 minutes while verifying the 5-minute replication RPO.