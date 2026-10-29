---
name: spring-api-authorisation
description: How to add or change an API endpoint in this Spring application without weakening authorisation.
---

# Spring API Authorisation

When creating or modifying an API endpoint:

1. Identify the existing authentication and authorisation mechanisms.
2. Determine the endpoint's required role, scope and resource-level permissions.
3. Check ownership and tenant boundaries where applicable.
4. Do not assume that authentication alone authorises resource access.
5. Verify whether method-level security is enabled before relying on method annotations.
6. Preserve existing access restrictions and avoid broadening security matchers unnecessarily.
7. Test both permitted and denied access paths.

Use the existing application's security patterns where appropriate.
