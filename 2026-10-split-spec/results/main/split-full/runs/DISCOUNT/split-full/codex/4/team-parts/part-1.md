Part 1 owns the discount domain and persistence/service layer.

Implement the store-scoped discount entity/model, repository/DAO wiring, service interface and implementation, validation, uniqueness/conflict handling, category validation, and calculation/evaluation API needed by the cart. Add any required Spring/JPA/XML wiring and model DTOs that are not HTTP-specific.

Own files under sm-core-model, sm-core, and persistence/configuration files needed solely for discounts. Do not edit controller, cart facade, mapper, or cart API files owned by parts 2/3.

Provide a usable service (for example DiscountService) with create/update/list/delete/find-by-code and an evaluation method that accepts the cart/store and returns applicability plus rounded discount/eligible subtotal. Part 2 will call CRUD methods; part 3 will call lookup/evaluation. Follow existing service/entity conventions and merchant-store scoping.
