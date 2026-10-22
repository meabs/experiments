---
name: verify-api
description: Verify a Shopizer REST/API change through the running Spring application and a client-like HTTP request.
---

# Verify REST behavior

For an API change, add or update a focused JUnit 4 integration test in `sm-shop/src/test/java/com/salesmanager/test/shop/integration` that calls the endpoint you changed. Call it with the same HTTP method, path, headers, authentication, and JSON/multipart body a client uses; assert both the status and the response body. The test should fail without your change and pass with it. `ServicesTestSupport` shows the admin login flow (`POST /api/v1/private/login`, then `Authorization: Bearer ...`) and helpers for the default `DEFAULT` store.

Run your test with:

```sh
mvn -o -pl sm-shop -am -Dtest=<YourTestClass> -DfailIfNoTests=false test
```

Use an integration test rather than a manually started server in this checkout. `sm-shop/src/test/java/com/salesmanager/test/shop/integration/system/ActuatorTest.java` shows the pattern: `@SpringBootTest(classes = ShopApplication.class, webEnvironment = WebEnvironment.RANDOM_PORT)`, an injected `TestRestTemplate`, and a request to the application. It only checks that the application starts, so running it does not verify a change. The test classpath supplies the in-memory H2 settings from `sm-shop/src/test/resources/database.properties`; startup also initializes the Shopizer reference data.

Standalone startup is not a working verification route here. `mvn -o -pl sm-shop -am spring-boot:run` runs the goal on the parent and fails because it has no main class. Running `mvn -o spring-boot:run` from `sm-shop` finds `ShopApplication` but fails because the default profile expects `classpath:database.properties`, which is only present in test resources; adding `-Dspring-boot.run.classpathScope=test` still fails with the same missing resource. Use the `@SpringBootTest` HTTP test instead, and do not claim a manual server check passed.
