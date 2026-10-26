Implement the product-question domain and business layer.

Own these files (create them as needed):
- sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/question/** (entity and status enum)
- sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/question/**
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/question/**

Add a JPA entity linking Product, Customer, and MerchantStore, with text, answer, status, asked/answered timestamps, and repository queries needed for customer, public, and admin ordering/filtering. Expose a Spring service (ProductQuestionService and implementation, or equivalent clearly named API) that validates/normalizes text and answers, enforces the 3 pending-question limit, handles ask/list/answer/reject, unknown SKU/id, rejected-answer conflict, and store scoping. Match existing service/repository conventions and ensure product deletion cascades/removes questions. Other parts rely on your public service methods and domain getters/setters; communicate any exact signatures in your completion message.
