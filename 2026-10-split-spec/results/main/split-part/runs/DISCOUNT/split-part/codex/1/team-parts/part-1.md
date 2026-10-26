Part 1 — discount domain and persistence

Implement the discount-code domain in the core modules. Own only files under `sm-core-model/src/main/java/com/salesmanager/core/model/discount/**` (and any new discount model package), `sm-core/src/main/java/com/salesmanager/core/business/repositories/discount/**`, and `sm-core/src/main/java/com/salesmanager/core/business/services/discount/**`. Add the entity, type enum, repository, service interface/implementation, validation, store scoping, case-insensitive uniqueness, and applicability/discount calculation needed by the cart integration. Add any required JPA mappings in these owned files; do not edit cart, API, or shop-model files.

Requirements (exact task wording):

- A code is JSON: {"code": "SPRING10", "type": "PERCENT" or "AMOUNT", "value": 10, "minimumSubtotal": 100.00, "startDate": "2026-01-01", "endDate": "2026-12-31", "categories": ["shoes"], "active": true}. "minimumSubtotal", "endDate" and "categories" are optional (category codes); "active" defaults to true; "startDate" defaults to today.
- Codes are unique within a store, ignoring case; creating or renaming to a code that already exists gives HTTP 409 Conflict. Different stores may use the same code.
- A PERCENT value must be more than 0 and at most 100; an AMOUNT value must be more than 0 (an amount in the store's currency). An end date before the start date, an unknown type or category, or a missing code or value gives HTTP 400 Bad Request.
- A code applies to a cart only if it belongs to the cart's store, is active, today is between its start and end dates (inclusive), the cart's subtotal is at least its minimum, and the cart has at least one eligible item.
- With categories, only items whose product is in one of those categories, or in any category below them, are eligible. Without categories, every item is.
- PERCENT takes that percentage off the eligible items' subtotal. AMOUNT takes that amount off, but never more than the eligible items' subtotal. The discount is rounded to 2 decimal places, halves rounding up.
- Test1234 no longer gives any discount, unless a merchant creates it as a code.

Provide stable public methods for other parts, at minimum methods to find a store/code case-insensitively, validate a candidate for create/update, delete by id and store, and evaluate an applied code against a `ShoppingCart` returning applicability and discount amount. Part 3 will call these methods from cart flows; Part 2 will call CRUD/validation methods from the admin API.
