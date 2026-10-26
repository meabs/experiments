# Part 2: shop DTOs, mapping, and facade

Read `TASK.md` first. Own the shop presentation/model layer for product questions: request/response DTOs, list envelope types, and a facade/populator or equivalent mapping service that converts the core question entity into the exact customer/admin JSON shape and the reduced public shape. Include ISO/date formatting consistent with the existing APIs, billing first-name attribution, trimmed text/answer handling as appropriate, and list ordering supplied by the core service. Add Spring wiring/beans only in your owned shop model/controller-facade/populator files.

Files owned: new or changed files under `sm-shop-model/src/main/java/com/salesmanager/shop/model/**` for question DTOs, and new or changed files under `sm-shop/src/main/java/com/salesmanager/shop/store/controller/**` (facade/populator packages) needed for mapping. Do not edit API controller classes under `sm-shop/src/main/java/com/salesmanager/shop/store/api/**`, and do not edit core model/service files.

Part 1 provides the core question entity, status, and service methods; use those rather than duplicating persistence rules. Part 3 will call your facade/DTO methods from the customer, public, and admin endpoints, so expose concise methods for each operation and response shape.
