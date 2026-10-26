Part 1 — discount domain, persistence, and business service

Implement the reusable discount-code domain and store-scoped persistence/service. Own only files under sm-core-model and sm-core needed for this (new discount model/repository/service/exception files and their module configuration); do not edit sm-shop controllers, DTOs, cart facade, cart mapper, or cart API. Follow existing Shopizer entity/service/repository conventions and make the service usable by both the admin API and cart code.

Requirements (copied from TASK.md):

Merchants want to run their own discount codes. Today the only code the shop understands is hard-coded in a rules file (Test1234), and it expired long ago. Replace it with discount codes that each store's admins manage themselves, and that shoppers apply to their cart.

- A code is JSON: {"code": "SPRING10", "type": "PERCENT" or "AMOUNT", "value": 10, "minimumSubtotal": 100.00, "startDate": "2026-01-01", "endDate": "2026-12-31", "categories": ["shoes"], "active": true}. "minimumSubtotal", "endDate" and "categories" are optional (category codes); "active" defaults to true; "startDate" defaults to today.
- Codes are unique within a store, ignoring case; creating or renaming to a code that already exists gives HTTP 409 Conflict. Different stores may use the same code.
- A PERCENT value must be more than 0 and at most 100; an AMOUNT value must be more than 0 (an amount in the store's currency). An end date before the start date, an unknown type or category, or a missing code or value gives HTTP 400 Bad Request.
- A code applies to a cart only if it belongs to the cart's store, is active, today is between its start and end dates (inclusive), the cart's subtotal is at least its minimum, and the cart has at least one eligible item.
- With categories, only items whose product is in one of those categories, or in any category below them, are eligible. Without categories, every item is.
- PERCENT takes that percentage off the eligible items' subtotal. AMOUNT takes that amount off, but never more than the eligible items' subtotal. The discount is rounded to 2 decimal places, halves rounding up.
- Test1234 no longer gives any discount, unless a merchant creates it as a code.

Provide clear class/method contracts for the other parts, at minimum a store-scoped lookup by code (case-insensitive), CRUD methods, and a method that evaluates an applicable code against a cart and returns the calculated discount/eligibility (or an equivalent result). Validate type/value/date/category and uniqueness here where practical; expose conflict/validation exceptions that Part 2 can map to HTTP statuses.

Other parts provide:
- Part 2 provides the HTTP/admin request/response DTOs and controller/facade; it will call your CRUD and validation methods.
- Part 3 provides cart integration and will call your case-insensitive lookup/evaluation service; it owns cart persistence/display changes.
