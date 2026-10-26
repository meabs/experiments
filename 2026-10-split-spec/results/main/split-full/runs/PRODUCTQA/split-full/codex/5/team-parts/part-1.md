Part 1: product-question domain and service layer.

Own these files (create the needed package files under these areas):
- sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/question/ (question entity/model and status enum)
- sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/question/
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/question/
- sm-shop-model/src/main/java/com/salesmanager/shop/model/catalog/product/question/ (request/response DTOs used by APIs)
- sm-shop/src/main/java/com/salesmanager/shop/populator/catalog/question/ (if a populator is useful)
- any required module pom/entity-scan/mapping updates directly needed for the above.

Implement persistence, store/product/customer associations, timestamps, status transitions, validation-supporting methods, and repository queries for customer newest-first, admin status/oldest-first, and public published newest-answered-first. Expose a coherent ProductQuestionService API (including create, customer list, public list, admin list, answer, reject) for the API parts. Trim/validate text and answer and enforce the three-PENDING-per-customer and rejected-answer conflict rules in the service. Do not add controllers.

The API parts rely on the service and DTO/model class names you establish; keep method names obvious and public. APIs will provide MerchantStore, Product/sku, Customer/principal, and map service exceptions to HTTP statuses. Product deletion must cascade/remove questions.
