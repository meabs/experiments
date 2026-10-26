Read TASK.md first. Own the admin REST API for /api/v1/private/discounts and its request/response DTOs/facade glue. Follow existing private APIs for store resolution and authorization. Implement POST (201 with id), GET list, PUT replacement, DELETE, correct 400/404/409 responses, JSON defaults and validation, and map to the discount service from Part 1. Do not edit cart endpoints/facades or the core discount persistence implementation.

Files owned: sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/discount/** (or the existing API package if you choose); sm-shop-model/src/main/java/com/salesmanager/shop/model/discount/**; and any narrowly scoped shop facade/mapper files solely required by this admin API. Avoid files owned by Parts 1 and 3. Use the public service/domain methods supplied by Part 1.

Part 1 supplies the store-scoped discount service and domain object. Part 3 owns shopper promo application and cart output.
