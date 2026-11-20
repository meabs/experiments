# Highly available GKE platform with a Cloud SQL analytics feed: design v4

## 1. Targets and design commitments

- End-to-end customer-facing availability target is 99.95% per calendar month (about 22 minutes of unavailability). This is an end-to-end SLO, not the result of multiplying nominal component SLAs.
- Initial, provisional monthly availability allocations total 22 minutes: application 5 minutes; GKE and node operations 4 minutes; load balancing 2 minutes; Cloud SQL 3 minutes; dependencies 2 minutes; planned maintenance 3 minutes; and regional failover/recovery 3 minutes. These are allocation targets, not independent component SLA claims. The team will define SLI measurement, attribution, overlap accounting, and exclusions before launch. Overlapping causes are charged once to the end-to-end budget. Exclusions are limited to documented customer-caused events and dependencies outside the agreed service boundary; maintenance and failover are not automatically excluded. Allocations are hypotheses to be revised using measured results.
- The platform must continue serving without manual intervention after loss of any one zone.
- Regional loss requires a documented and rehearsed recovery with a 15-minute RTO and a 5-minute RPO. The RPO is conditional on cross-region replica lag remaining within five minutes. If lag exceeds that limit, the incident procedure withdraws the five-minute RPO claim, acknowledges and records the larger possible data loss and last confirmed replicated position, and requires an explicit incident decision before promotion.
- Peak traffic is approximately 5,000 requests/second. The team consists of eight engineers using managed services wherever practical.

## 2. GKE topology and networking

- The primary workload runs in a regional GKE Standard cluster in `europe-west2`, with nodes distributed across all three zones.
- Separate system and application node pools use cluster autoscaling. Maximum node counts include zone-loss operation, rolling-upgrade surge, and growth headroom.
- The Pod secondary range will be sized from the selected GKE alias-IP/per-node allocation settings, maximum nodes, surge capacity, and projected growth. The `/22` in version 1 is rejected. The final range size and IP-allocation calculation must be recorded before provisioning; a candidate such as `/19` is only an example, not an unvalidated commitment.
- Nodes are private. Control-plane access is restricted to authorised networks. Internet egress uses Cloud NAT with the required regional capacity and monitoring.
- Use the Regular GKE release channel, or Stable if it meets the required versions and features. The selected channel, upgrade policy, maintenance window, and rollback procedure must be validated in staging. A maintenance window does not eliminate all maintenance disruption.

## 3. Capacity and placement

- Six replicas at 800 requests/second provide only 4,800 requests/second and are not sufficient headroom for a 5,000-request/second peak. Replica count and pod resources will be increased based on load-test results, with capacity for peak traffic, one-zone loss, rolling upgrades, and autoscaler delay.
- Capacity will be tested at peak and during loss of each zone. The design must leave adequate CPU, memory, IP, and node capacity in the two surviving zones; 90% utilisation is not accepted as an unvalidated safety margin.
- Stateless tiers use topology spread constraints across zones and required hostname anti-affinity where one replica per node is required. Scheduling behavior when constraints cannot be met is explicitly tested.
- PodDisruptionBudgets permit planned maintenance while preserving the tested serving capacity; `minAvailable: 6` for six replicas is not used. The final value is based on the revised replica count, zone-loss capacity, and drain tests.
- Node pools use surge upgrades with settings sized to the available IP and compute capacity. Upgrade and drain tests verify that PDBs do not block routine maintenance indefinitely.

## 4. Traffic and regional recovery

- User traffic enters through a global external Application Load Balancer with explicitly configured health-based backend failover/routing. The design does not depend on changing DNS to a regional address during an incident.
- Health checks test meaningful application readiness, including required dependency behavior, rather than merely process liveness. Connection draining and failover thresholds are tested.
- The recovery region is continuously provisioned, readiness-tested, capacity-tested, and drift-validated. This includes the cluster control plane, minimum node capacity for the tested failover load, workload manifests, networking, load-balancer integration, secrets, certificates, images, policies, observability, and autoscaling. Artifacts are continuously deployable. Additional capacity created after regional loss cannot count toward the 15-minute RTO unless its provisioning time is measured within that RTO.
- Regional recovery is automated where safe and otherwise follows a documented runbook. The runbook includes detection, traffic failover, Cloud SQL promotion, application database-endpoint/configuration change, credential handling, fencing or write prevention against the failed primary, smoke tests, and rollback/failback.
- Normal Cloud SQL promotion eligibility requires healthy validated replication, a confirmed replay position, and replica lag of no more than 60 seconds. Lag from 60 seconds through five minutes requires incident-commander approval and recording of the measured possible loss. If lag exceeds five minutes, the conditional five-minute RPO is withdrawn; promotion is delayed or proceeds only as an explicit incident decision with stakeholder acceptance and recorded possible loss.
- The recovery rehearsal measures detection, provisioning/readiness, database promotion, configuration propagation, traffic convergence, and validation. The measured total must fit the 15-minute RTO. DNS with a 3,600-second TTL is not part of the critical failover path; any DNS used operationally has a low, tested TTL and resolver-caching assumptions.

## 5. Cloud SQL

- Cloud SQL for PostgreSQL uses regional high availability, with automatic in-region failover. The HA standby is not used as a reporting endpoint.
- Analytics uses a separately provisioned, supported read replica or another supported export architecture. Replica load and lag are monitored, and dashboards tolerate read staleness.
- A cross-region asynchronous read replica in `europe-west1` is maintained for regional recovery. Monitoring alerts before replica lag reaches five minutes, and the runbook defines escalation, promotion eligibility, validated replication state, and the degraded-RPO response when the threshold is exceeded. Promotion eligibility, replication state validation, promotion time, and application reconnection are tested.
- The RPO is reported from measured replica lag and is not guaranteed merely by creating a replica. The recovery procedure records the last confirmed replicated position and the possible data-loss interval.
- Automated backups and point-in-time recovery are enabled. Backup restoration is not assumed to take five minutes regardless of database size. Restore, replay, validation, and cutover times are measured for representative database sizes and documented as separate recovery objectives.

## 6. Change data capture and BigQuery

- Datastream reads committed changes from Cloud SQL using the supported PostgreSQL logical-decoding configuration. Required flags, privileges, publication/slot configuration, and version compatibility are documented and tested.
- Source commit-to-BigQuery availability is measured end to end. The target freshness is approximately five minutes, with alerts at three minutes and a defined escalation at five minutes.
- Replication-slot and WAL-retention limits are monitored. Datastream backpressure must not exhaust primary storage or otherwise endanger transactional availability. The runbook defines bounded retention, destination recovery, replay/backfill, and the response when the retained WAL window is exceeded.
- During Cloud SQL failover or regional promotion, Datastream is paused or reconfigured as required, the source endpoint and logical-decoding position are validated, and CDC is resumed only after duplicate, missing, ordering, update, delete, and schema-change behavior is verified. BigQuery freshness is rechecked after recovery.
- The destination processing is idempotent, but a primary-key merge alone is not treated as proof of correct event ordering or delete handling. Event identity, ordering/reconciliation, tombstones, and backfill procedures are defined.
- BigQuery data-staleness settings are chosen to meet the freshness objective rather than solely to reduce query cost.

## 7. Security

- Workloads use Workload Identity Federation for GKE, with one least-privilege Google service account per tier and no exported keys.
- Network policies deny cross-namespace traffic by default. Binary Authorization admits only images built and attested by the approved pipeline.
- Personal-data columns use BigQuery policy tags. Datasets use customer-managed encryption keys with documented key availability, rotation, and recovery procedures.

## 8. Observability and operational controls

- SLIs are load-balancer request success rate and latency, with dependency and application indicators included for diagnosis. Alerts cover one-hour and six-hour error-budget burn, zone capacity, scheduling failures, autoscaler state, load-balancer backend health, Cloud SQL failover state, replica lag, backup status, Datastream lag/freshness, slot/WAL retention, and BigQuery availability.
- Runbooks cover zone loss, regional loss, Cloud SQL promotion, stale or failed CDC, WAL-retention risk, backup restore, and failback.
- Configuration, secrets, database endpoints, and recovery-region artifacts are continuously validated for drift.

## 9. Testing and approval gates

- Load tests cover 5,000 requests/second plus agreed headroom, normal operation, one-zone loss, node failure, rolling upgrades, PDB behavior, autoscaler delay, and recovery-region capacity.
- A zone-failure game day runs at least quarterly. A full regional recovery rehearsal runs at least annually and measures the 15-minute RTO, conditional five-minute RPO, traffic convergence, database promotion, application reconfiguration, and CDC recovery.
- Backup restores are tested at representative sizes. Cloud SQL replica promotion and Datastream pause/reconfiguration/replay are tested, including the 60-seconds-to-five-minutes approval path and the above-five-minutes degraded-RPO path.
- Build approval requires recorded results for the provisional availability-budget review, including measurement and overlap/exclusion rules; IP-range sizing; capacity; failover timings; replica lag/RPO; restore timing; CDC freshness; and all identified failure-mode runbooks.