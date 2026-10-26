Part 2 owns the admin HTTP API and its shop-facing request/response model.

Implement protected /api/v1/private/discounts POST/GET/PUT/{id}/DELETE/{id}, including ?store= scoping, HTTP 201 create, validation/error status mapping (400/409), and serialization of the specified JSON fields/defaults. Add controller/facade/DTO files under sm-shop and sm-shop-model as needed, using the DiscountService contract from part 1.

Own only admin discount API/controller/facade and HTTP DTO/mapper files. Do not edit core discount persistence/service files (part 1) or shopping-cart facade/API/mapper/calculation files (part 3). Ensure update/delete cannot cross stores and duplicate codes are case-insensitive.
