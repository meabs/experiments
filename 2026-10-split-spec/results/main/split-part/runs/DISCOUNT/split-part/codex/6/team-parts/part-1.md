# Part 1 — discount domain, persistence, and admin CRUD

## Scope and owned files

Own the new discount domain end to end: the persistent model and repository in `sm-core-model`/`sm-core`, the service implementation and validation, shop-layer request/response DTOs and facade, and the `/api/v1/private/discounts` controller. You may add files in those areas and modify only files needed for this part. Do not edit cart facade/mapper/calculation files owned by parts 2 or 3.

## Requirements (exact task wording)

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- POST /api/v1/private/discounts creates a code and returns HTTP 201 with the stored code, including its "id".
- GET /api/v1/private/discounts lists the store's codes.
- PUT /api/v1/private/discounts/{id} replaces a code; DELETE /api/v1/private/discounts/{id} removes it.
- A code is JSON: {"code": "SPRING10", "type": "PERCENT" or "AMOUNT", "value": 10, "minimumSubtotal": 100.00, "startDate": "2026-01-01", "endDate": "2026-12-31", "categories": ["shoes"], "active": true}. "minimumSubtotal", "endDate" and "categories" are optional (category codes); "active" defaults to true; "startDate" defaults to today.

Rules:

- Codes are unique within a store, ignoring case; creating or renaming to a code that already exists gives HTTP 409 Conflict. Different stores may use the same code.
- A PERCENT value must be more than 0 and at most 100; an AMOUNT value must be more than 0 (an amount in the store's currency). An end date before the start date, an unknown type or category, or a missing code or value gives HTTP 400 Bad Request.

## Contracts for other parts

Expose a Spring service (for example `DiscountService`) that can find a code case-insensitively for a `MerchantStore`, list/save/replace/delete by store and id, and validate whether referenced category codes exist. The cart/calculation parts will inject this service; keep DTO date/category values readily convertible to `LocalDate` and expose the merchant-written code and id.

Use the project’s existing private API store resolution, exception, and response conventions. Ensure create explicitly returns 201 and duplicate conflicts map to 409 while validation maps to 400.
