Implement customer-authenticated and public product-question HTTP APIs plus transport DTOs.

Own these files (create them as needed):
- sm-shop-model/src/main/java/com/salesmanager/shop/model/catalog/product/question/**
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductQuestionApi.java (or split customer/public controllers under this package)

Provide POST /api/v1/auth/products/{sku}/questions, GET /api/v1/auth/customer/questions, and GET /api/v1/products/{sku}/questions with exact response shapes/statuses, authentication behavior, trimming/validation errors, SKU 404, and ordering from TASK.md. Use ProductQuestionService from part 1 and existing Principal/customer/store resolution patterns. Do not implement private admin endpoints. Keep DTO JSON fields exactly as specified.
