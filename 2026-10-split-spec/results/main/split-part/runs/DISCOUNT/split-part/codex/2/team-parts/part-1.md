Part 1 — discount domain, persistence, and business service

Own these files/directories (and only these unless a compile fix is strictly required): `sm-core-model/src/main/java/com/salesmanager/core/model/discount/**`, `sm-core/src/main/java/com/salesmanager/core/business/repositories/discount/**`, and `sm-core/src/main/java/com/salesmanager/core/business/services/discount/**` (plus matching persistence configuration/migration resources if needed).

Implement the stored discount-code entity/enum, repository, and service used by both the admin API and cart code. The service should expose clear methods such as `create`, `update`, `delete`, `listByStore`, `findByCode(store, code)`, and an applicability/discount calculation method that cart code can call. Enforce all validation and case-insensitive per-store uniqueness here, resolve category codes and descendants, and preserve the merchant-written code spelling. Make persistence tenant-scoped by merchant store.

Exact task requirements for this part:

- A code is JSON: {"code": "SPRING10", "type": "PERCENT" or "AMOUNT", "value": 10, "minimumSubtotal": 100.00, "startDate": "2026-01-01", "endDate": "2026-12-31", "categories": ["shoes"], "active": true}. "minimumSubtotal", "endDate" and "categories" are optional (category codes); "active" defaults to true; "startDate" defaults to today.
- Codes are unique within a store, ignoring case; creating or renaming to a code that already exists gives HTTP 409 Conflict. Different stores may use the same code.
- A PERCENT value must be more than 0 and at most 100; an AMOUNT value must be more than 0 (an amount in the store's currency). An end date before the start date, an unknown type or category, or a missing code or value gives HTTP 400 Bad Request.
- A code applies to a cart only if it belongs to the cart's store, is active, today is between its start and end dates (inclusive), the cart's subtotal is at least its minimum, and the cart has at least one eligible item.
- With categories, only items whose product is in one of those categories, or in any category below them, are eligible. Without categories, every item is.
- PERCENT takes that percentage off the eligible items' subtotal. AMOUNT takes that amount off, but never more than the eligible items' subtotal. The discount is rounded to 2 decimal places, halves rounding up.

Other parts provide the REST DTO/controller and invoke this service from cart application/calculation. Coordinate on method signatures and exceptions; part 2 relies on conflict/validation exceptions, and part 3 relies on lookup plus a calculation result containing discount amount and eligibility.
