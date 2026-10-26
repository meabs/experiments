Part 1 – discount domain and persistence/service

Implement the discount-code domain used by the admin API and cart. Own all new/changed files under sm-core-model/src/main/java/.../discount (or equivalent core model package), sm-core/src/main/java/.../business/repositories/discount, and sm-core/src/main/java/.../business/services/discount, plus required JPA/config files in those modules. Do not edit shop controllers or cart facade/populator files.

Requirements (exact task wording):
- A code is JSON: {"code": "SPRING10", "type": "PERCENT" or "AMOUNT", "value": 10, "minimumSubtotal": 100.00, "startDate": "2026-01-01", "endDate": "2026-12-31", "categories": ["shoes"], "active": true}. "minimumSubtotal", "endDate" and "categories" are optional (category codes); "active" defaults to true; "startDate" defaults to today.
- Codes are unique within a store, ignoring case; creating or renaming to a code that already exists gives HTTP 409 Conflict. Different stores may use the same code.
- A PERCENT value must be more than 0 and at most 100; an AMOUNT value must be more than 0 (an amount in the store's currency). An end date before the start date, an unknown type or category, or a missing code or value gives HTTP 400 Bad Request.

Expose clear service methods for API/cart integration (e.g. create/update/delete/list/findByStoreAndCodeIgnoreCase and validate/apply eligibility). Persist store ownership, dates, active flag, type/value, optional minimum and category codes. Category validation must resolve category codes and support descendants for cart eligibility. Preserve merchant-written code casing.

Other parts provide/consume: Part 2 calls the service CRUD/validation methods and maps the model to JSON; Part 3 calls case-insensitive lookup and eligibility/discount calculation methods while rendering carts.
