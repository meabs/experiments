## Part 1: product-question persistence and service

Read `TASK.md` first. Own the product-question domain and service layer. Add the JPA entity/status representation, repository, service interface/implementation, and shopizer model wiring needed to persist questions. Ensure product deletion cascades/removes its questions without breaking existing product behavior.

Files owned (create or edit only these, plus narrowly required package-local test files):
- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/question/**` (new entity/status classes)
- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/Product.java` (question relationship/cascade)
- `sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/question/**`
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/question/**`

Provide a service contract usable by both REST parts. It should support creating a trimmed validated question for a customer/product/store, listing by customer newest-first, listing by store/status oldest-first, listing published questions for a product newest-answered-first, answering (including replacing an existing published answer), rejecting, and lookup by id. Expose clear methods (for example `create`, `getByCustomer`, `getByStoreAndStatus`, `getPublishedByProduct`, `answer`, `reject`, `getById`) and status constants/enum. Enforce domain invariants where practical (pending limit, rejected-answer conflict, unknown entities via null/exception) while allowing API layers to map HTTP errors.

Other parts rely on these entity getters/setters and service methods; keep names straightforward and document any deviations in your completion message. Do not edit REST DTOs/controllers.
