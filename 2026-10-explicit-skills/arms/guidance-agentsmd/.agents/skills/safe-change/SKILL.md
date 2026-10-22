---
name: safe-change
description: Plan and review changes to Shopizer request flow, domain/persistence layers, shared code, or REST error behavior.
---

# Change Shopizer safely

## Follow the request through the layers

For a REST request, start in the `@RestController` under `sm-shop/src/main/java/com/salesmanager/shop/store/api` (usually `/api/v1` or `/api/v2`). Security filters and the application security configuration may authenticate or reject the request before the controller. The controller normally delegates to a facade under `sm-shop/src/main/java/com/salesmanager/shop/store/controller/**/facade`, which handles orchestration, authorization checks, DTO conversion, and populators. Reusable business operations belong in a service interface/implementation under `sm-core/src/main/java/com/salesmanager/core/business/services`; persistence belongs in a Spring Data repository or custom repository under `sm-core/src/main/java/com/salesmanager/core/business/repositories`. Entities are in `sm-core-model`; API request/response models are in `sm-shop-model`.

Choose the narrowest layer that owns the behavior: route binding and request validation in the API controller, API mapping/orchestration in the facade, domain rules in the core service, and query/update mechanics in the repository. Keep API models and core entities separate and preserve the existing facade/service contracts when the behavior is reusable. Watch for the two customer facade contracts: `com.salesmanager.shop.store.controller.customer.facade.CustomerFacade` is the main API facade, while `com.salesmanager.shop.store.controller.customer.facade.v1.CustomerFacade` is a separate reset-password contract used by the v1 facade.

## Understand HTTP errors

REST controllers under `com.salesmanager.shop.store.api` are covered by `RestErrorHandler` (`sm-shop/src/main/java/com/salesmanager/shop/store/api/exception/RestErrorHandler.java`):

- `ResourceNotFoundException` becomes 404.
- `UnauthorizedException` becomes 401.
- `ConversionRuntimeException`, `ServiceRuntimeException`, and `RestApiException` become 400.
- An otherwise unhandled `Exception` becomes 500.

These handlers return an `ErrorEntity` JSON body with an error code and message. The separate `ShopErrorController` advice for `com.salesmanager.shop.store.controller` renders error views and returns 500, so do not assume every exception in the application follows the REST JSON mapping. File-upload failures have their own `FileUploadExceptionAdvice`.

When changing an exception, status, or error body, inspect the actual exception class, all throw sites, the advice handler, and a client-facing integration test. Check authentication and authorization paths as well as the happy path.

## Audit shared code before editing it

Before changing a public interface, shared service, entity, DTO, populator, exception, or repository method, search all modules for its declaration, imports, implementations, callers, tests, and configuration references. For example:

```sh
rg -n "CustomerService|CustomerFacade" sm-core sm-shop sm-shop-model -g '*.java'
```

Use the same search with the exact symbol or route being changed; also search XML/properties when configuration may be involved. Inspect every implementation and caller found, including security services, other API versions, populators, and integration tests. Add or update the smallest relevant unit/integration test, then run the focused class check and `mvn -o test` when the change crosses module boundaries or changes shared behavior.

Before handoff, review `git diff`, run:

```sh
git diff --check
```

and confirm `git status --short` contains only intentional source/test/documentation changes. Integration tests can modify generated data under `sm-shop/files`; distinguish and clean up only changes created by the test run.
