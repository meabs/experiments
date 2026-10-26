Part 1: stock-alert domain, persistence, and business service.

Implement the stock alert and outbox data model, repositories, DTOs/mappers as needed, and a service usable by both APIs and inventory updates. The service must support creating/canceling alerts, filtering/listing alerts and outbox messages, case-insensitive pending deduplication, and dispatching all pending alerts when a product transitions from zero to positive stock. Keep tenant/store scoping and product name lookup in this layer. Ensure product deletion cascades/removes associated alerts if that requires domain-service changes.

Own these files/directories (new files are expected under the corresponding packages):
- sm-core-model/src/main/java/com/salesmanager/core/model/... stock-alert entities
- sm-core/src/main/java/com/salesmanager/core/business/repositories/... stock-alert repositories
- sm-core/src/main/java/com/salesmanager/core/business/services/... stock-alert service and implementation
- sm-shop-model/src/main/java/com/salesmanager/shop/model/... stock-alert API DTOs
- sm-shop/src/main/java/com/salesmanager/shop/mapper/... stock-alert mappers, if needed
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductServiceImpl.java only for alert cleanup on product deletion, if needed

Other parts provide/use these contracts: Part 2 will call the alert service methods for shopper create/cancel and admin list/outbox; expose clear methods and result/status types. Part 3 will call a method such as dispatchPendingAlerts(product, previousQuantity, newQuantity) after inventory persistence and will rely on alert cleanup being safe during product deletion.
