Task for this session: produce a detailed design document for a highly available Google Kubernetes Engine (GKE) cluster platform.

Context: a customer-facing web application (stateless API and web tier, plus a stateful relational database and a
message queue) for users in one continent. Target: 99.95% monthly availability for the service. Peak traffic is about
5,000 requests a second. The platform must survive the loss of a single zone without anyone having to intervene, and a
loss of a whole region must have a documented, rehearsed recovery. The team is eight engineers on a managed-service budget.

The document should be something a platform team could build from. It should cover at least: cluster and node topology;
workload placement and disruption handling; traffic entry; the stateful data tier; failure behaviour (zone and region);
upgrades and maintenance; networking; observability and service-level objectives; security that affects availability;
testing of failures; and the risks, assumptions and trade-offs you accept.

The shared document starts empty. Write it together and agree a version.
