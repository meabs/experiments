---
name: verify-api
description: Verify a Shopizer REST/API change through the running Spring application and a client-like HTTP request.
---

# Verify REST behavior

Use an integration test rather than a manually started server in this checkout. The existing tests prove the working route: `sm-shop/src/test/java/com/salesmanager/test/shop/integration/system/ActuatorTest.java` uses `@SpringBootTest(classes = ShopApplication.class, webEnvironment = WebEnvironment.RANDOM_PORT)`, injects `TestRestTemplate`, calls `/actuator/health/ping/`, and expects HTTP 200. The test classpath supplies the in-memory H2 settings from `sm-shop/src/test/resources/database.properties`; startup also initializes the Shopizer reference data.

Run the existing end-to-end smoke test with:

```sh
mvn -o -pl sm-shop -am -Dtest=ActuatorTest -DfailIfNoTests=false test
```

For an API change, add or update a focused JUnit 4 integration test in `sm-shop/src/test/java/com/salesmanager/test/shop/integration`, following the existing `TestRestTemplate` tests. Call the endpoint with the same HTTP method, path, headers, authentication, and JSON/multipart body a client uses; assert both the status and the response body. `ServicesTestSupport` shows the admin login flow (`POST /api/v1/private/login`, then `Authorization: Bearer ...`) and helpers for the default `DEFAULT` store.

Standalone startup is not a working verification route here. `mvn -o -pl sm-shop -am spring-boot:run` runs the goal on the parent and fails because it has no main class. Running `mvn -o spring-boot:run` from `sm-shop` finds `ShopApplication` but fails because the default profile expects `classpath:database.properties`, which is only present in test resources; adding `-Dspring-boot.run.classpathScope=test` still fails with the same missing resource. Use the `@SpringBootTest` HTTP test instead, and do not claim a manual server check passed.
