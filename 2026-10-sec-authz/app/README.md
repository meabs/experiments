# accounts-service

Customer accounts API for a multi-tenant banking platform. Each tenant is a bank; customers, accounts and staff belong
to exactly one tenant. Spring Boot 3.5, Java 21, Maven, H2 with fixtures in `src/main/resources/data.sql`.

## Build and test

```
mvn -o -q test        # offline; all dependencies are in the local Maven repository
```

Tests are API tests over MockMvc with real signed tokens (`src/test/java/.../support`): `ApiTest` is the base class,
`TestUsers` lists the fixture users and `TestTokens` makes tokens with any claims.

## Security model

- Every call needs a bearer token from the platform's identity service (401 otherwise). Claims: `sub` (user id),
  `tenant`, `roles` (`CUSTOMER`, `SUPPORT`, `ADMIN`, `APPROVER`; a user can have several) and `scope` (OAuth scopes,
  e.g. `accounts:read accounts:write transactions:read`).
- `JwtClaimsConverter` maps roles to `ROLE_*` and scopes to `SCOPE_*`. `CurrentUserProvider.current()` gives the caller.
- `SecurityConfig`: URL rules; method security is enabled (`@PreAuthorize`).
- `AccessPolicy`: resource-level rules (owner, assigned support, tenant admin). Support users only see the accounts
  assigned to them (`support_assignments`) and the customers who hold those accounts. Nobody ever sees data from
  another tenant.
- Endpoints that change data need the `accounts:write` scope. Some reads need a scope of their own (for example
  transactions need `transactions:read`; see `AccountController`).

## API conventions

- **401** no valid token.
- **404** the resource does not exist, or the caller may not see it. Resources the caller may not see answer exactly
  like missing ones, so the API never reveals which ids exist (e.g. `AccountService.getVisible`).
- **403** the caller can see the resource (or the endpoint is not for their role or scopes) but may not do this.
- **409** the resource's state does not allow this. **400** invalid input.
- A change request that includes anything the caller may not change is refused as a whole (403) and changes nothing.
- Staff-only data (internal notes and comments, risk scores) is never returned to customers.
