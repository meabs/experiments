# The estate (base version)

Four independently deployable services (`customer`, `decision`, `ledger`, `notifier`), plain Java 21, JUnit 5, H2. Each
is its own Maven project (`mvn -o verify`). They run on a platform that supplies a database per service (shared by
all instances and versions), synchronous calls between services, and asynchronous events.
Service contracts are in `contracts/`. The platform code is not part of this repository.
