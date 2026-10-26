Part 2: protected admin REST API for product quantity tiers.

Own these files (and any new files in the same API/model packages needed for this part):
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/* (add the tiers endpoint/controller here; avoid unrelated endpoint edits)
- new request/response DTO files under sm-shop-model/src/main/java/com/salesmanager/shop/model/catalog/product or an appropriate product package

Implement PUT /api/v1/private/product/{id}/tiers and GET of the same path, using the existing private endpoint protection and @ApiIgnore MerchantStore resolution patterns. PUT replaces all tiers and returns HTTP 200 with ordered stored tiers; GET returns ordered tiers. Unknown or cross-store product must be 404. Map malformed/invalid tier payloads and service validation failures to 400, with rejected PUT leaving existing tiers unchanged. Accept empty list to clear tiers. JSON fields are minQuantity and price.

Relies on Part 1's tier entity/service methods and ProductService.retrieveById/findOne/store ownership behavior. Part 3 is independent except that cart repricing will observe tiers changed through this API.
