## Part 1: stock-alert domain and core service

Implement the persistent stock-alert/outbox domain and business rules in the core modules. Add the alert and outbox entities, repositories, service interface/implementation, and any core-model DTO/enums needed by the APIs. The service must support creating/cancelling/listing alerts, validating stock state and email uniqueness (case-insensitive), and sending all pending alerts when an inventory transition goes from quantity zero to positive; it must create one outbox record per alert, set sent timestamps/status exactly once, and remove alerts with product deletion.

Own files under `sm-core-model/src/main/java/com/salesmanager/core/model/...` and `sm-core/src/main/java/com/salesmanager/core/business/...` for this domain (including repository/service files and product-delete integration). Do not edit API/controller or shop facade files owned by other parts.

Part 3 will call the service hook you provide (use a clear method such as `onInventoryUpdated(ProductAvailability previous, ProductAvailability current)` or equivalent) after saving inventory. Part 2 will inject the service and use its public methods to implement the HTTP resources.
