# Shopizer agent guidance

Shopizer is a Java 11-targeted, Spring Boot 2.5.12 e-commerce platform. The Maven reactor is:
`sm-core-model` (domain entities), `sm-core-modules` (shared modules), `sm-core` (services and JPA repositories), `sm-shop-model` (API models), and `sm-shop` (Spring Boot web/API application and integration tests). `ShopApplication` is in `sm-shop`.

Run Maven offline from the repository root. The useful checks are `mvn -o -DskipTests package` for the reactor/package and `mvn -o test` for the full build and tests. To run one `sm-shop` test class, use `mvn -o -pl sm-shop -am -Dtest=ActuatorTest -DfailIfNoTests=false test` (the flag is needed because upstream modules have no matching test). See `.agents/skills/build-test/SKILL.md` for the full test workflow.

Use `.agents/skills/verify-api/SKILL.md` for endpoint/client behavior. Use `.agents/skills/safe-change/SKILL.md` before changing request flow, persistence, shared services/models, or error handling.
