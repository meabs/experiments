# Part 1 — discount domain, persistence, and service

## Scope and owned files

Own all new or modified files under `sm-core-model/src/main/java/com/salesmanager/core/model/discount/` (and any directly necessary core-model mapping files), plus all new or modified discount repository/service files under `sm-core/src/main/java/com/salesmanager/core/business/repositories/discount/` and `sm-core/src/main/java/com/salesmanager/core/business/services/discount/`. Do not edit shop API, shop DTO, cart facade/mapper, or order-total files owned by the other parts.

Implement a persisted store-scoped discount code entity (including id, merchant store, code, type, value, optional minimum subtotal, start/end dates, category codes, active) and repository/service operations. Expose a Spring service named `DiscountService` (implementation `DiscountServiceImpl`) with methods the other parts can call: create/save, update/replace, delete, list by store, and lookup by code/store ignoring case; include validation and a way to evaluate a code against cart items/store/date and return the computed positive discount. Use existing MerchantStore, Product, Category, shopping-cart and repository conventions. Enforce uniqueness within one store case-insensitively and all task validation/category/date/type/value rules here where practical; throw clear exceptions that the API can translate to 400/409.

## Exact task requirements applying to this part

Merchants want to run their own discount codes. Today the only code the shop understands is hard-coded in a rules file (Test1234), and it expired long ago. Replace it with discount codes that each store's admins manage themselves, and that shoppers apply to their cart.

- A code is JSON: {"code": "SPRING10", "type": "PERCENT" or "AMOUNT", "value": 10, "minimumSubtotal": 100.00, "startDate": "2026-01-01", "endDate": "2026-12-31", "categories": ["shoes"], "active": true}. "minimumSubtotal", "endDate" and "categories" are optional (category codes); "active" defaults to true; "startDate" defaults to today.

Rules:

- Codes are unique within a store, ignoring case; creating or renaming to a code that already exists gives HTTP 409 Conflict. Different stores may use the same code.
- A PERCENT value must be more than 0 and at most 100; an AMOUNT value must be more than 0 (an amount in the store's currency). An end date before the start date, an unknown type or category, or a missing code or value gives HTTP 400 Bad Request.
- A code applies to a cart only if it belongs to the cart's store, is active, today is between its start and end dates (inclusive), the cart's subtotal is at least its minimum, and the cart has at least one eligible item.
- With categories, only items whose product is in one of those categories, or in any category below them, are eligible. Without categories, every item is.
- PERCENT takes that percentage off the eligible items' subtotal. AMOUNT takes that amount off, but never more than the eligible items' subtotal. The discount is rounded to 2 decimal places, halves rounding up.

Test1234 no longer gives any discount, unless a merchant creates it as a code.

## What other parts provide / rely on

Part 2 will map its request/response DTO to your entity and call `DiscountService` CRUD methods; preserve public method names/signatures and provide id on save. Part 3 will call your case-insensitive lookup/evaluation method from cart application and total calculation, and needs an explicit result containing applicability, eligible subtotal, and rounded discount.
