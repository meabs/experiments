---
name: build-test
description: Build Shopizer or run its Maven tests, including one test class, using the repository's offline reactor and local Maven cache.
---

# Build and test Shopizer

Run commands from the repository root. Maven is configured with remote repositories in the POM, but this checkout is offline; always use `-o`.

## Build

To compile, package every module, and create the runnable `sm-shop/target/shopizer.jar` without running tests:

```sh
mvn -o -DskipTests package
```

The reactor order is `sm-core-model`, `sm-core-modules`, `sm-core`, `sm-shop-model`, then `sm-shop`. A successful command ends with `BUILD SUCCESS`.

## Full test run

The normal validation command is:

```sh
mvn -o test
```

This builds the whole reactor and runs both the `sm-core` tests and the `sm-shop` tests. Some older core and shop tests are annotated `@Ignore`, so skipped tests in the summary are expected; do not treat them as passing coverage.

## One class

For one `sm-shop` test class, use its simple class name with the reactor dependencies:

```sh
mvn -o -pl sm-shop -am -Dtest=ActuatorTest -DfailIfNoTests=false test
```

Replace `ActuatorTest` with the target class, for example an integration test under `sm-shop/src/test/java`. `-am` builds the upstream modules, and `-DfailIfNoTests=false` prevents those upstream modules, which have no matching class, from failing the run. The verified class above starts the application on a random port and passes one test.

After any test run, inspect `git status --short`: the application initializes H2 data and file-backed content during integration tests, so test-created changes under `sm-shop/files` must not be mistaken for source changes. Preserve unrelated pre-existing user changes.
