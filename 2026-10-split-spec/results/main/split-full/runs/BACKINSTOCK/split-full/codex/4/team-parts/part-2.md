## Part 2: shopper and admin HTTP APIs

Implement the v1 REST resources and shop-facing DTOs for stock alerts. Add POST/DELETE `/api/v1/products/{sku}/alerts` (public, store resolved from `?store=`) and authenticated GET `/api/v1/private/stock-alerts` plus `/outbox`, including response shapes, status codes, email/status filtering and validation/error mapping required by `TASK.md`.

Own files under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/...` and `sm-shop/src/main/java/com/salesmanager/shop/model/...` that are specifically for stock alerts; add focused mapper/populator classes there if useful. Do not edit core entities/services or inventory facade files owned by Parts 1 and 3.

Part 1 provides the alert service and its methods for create/cancel/list/outbox (and domain objects). Use the existing `MerchantStore`/`Language` injection and security conventions from neighboring v1 APIs.
