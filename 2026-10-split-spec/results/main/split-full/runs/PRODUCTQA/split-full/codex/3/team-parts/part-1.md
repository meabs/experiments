Part 1 owns the product-question domain and persistence layer. Read TASK.md first.

Own these files (create or modify only these, plus narrowly required package-local support files):
- sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/question/ProductQuestion.java
- sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/question/ProductQuestionRepository.java
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/question/ProductQuestionService.java
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/question/ProductQuestionServiceImpl.java
- sm-shop-model/src/main/java/com/salesmanager/shop/model/catalog/product/question/Question DTO/request/response classes

Implement the entity, status enum, repository queries, service operations and DTOs needed by all APIs. Service API should expose clear methods for asking by SKU/customer/store, finding a customer's questions, listing by store/status, public published questions by SKU, answering, rejecting, and id lookup; enforce trimming, length limits, pending limit, unknown SKU/id, rejected-answer conflict, and store scoping. DTOs must serialize exactly the customer/admin and public shapes in TASK.md. Keep product deletion safe (questions should cascade or be removed with their product). Other parts rely on the service and DTO class/method names you provide, so keep them public and straightforward and report them when done.

Other parts provide the HTTP controllers and authenticated principal/store handling. They rely on this part's service and DTOs; do not edit controller files.
