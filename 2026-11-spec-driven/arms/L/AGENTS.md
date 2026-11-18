# Working in this repository

- Read the whole ticket and list each requirement before you start. Meet every one.
- Read the code involved and follow its existing patterns.
- Keep the change to what the ticket asks.
- Add or update tests for what you changed.
- Build and run the tests before you finish, and fix anything you broke.
- In your summary, say what you changed, what you checked, and anything you couldn't do.
- Skills in .agents/skills: requirements-check (at the start and end of a ticket), build-and-verify (before you
  finish), self-review (read your diff before you finish).

## Reference notes

The notes below are general background for this repository and for working in it.

### Repository overview

Shopizer is an open-source Java e-commerce platform built with Maven. It is a multi-module build:
- `sm-core-model`: domain entities and enums shared by the other modules.
- `sm-core-modules`: pluggable modules such as payment, shipping and integration providers.
- `sm-core`: services, repositories and business logic.
- `sm-shop-model`: the REST request and response objects.
- `sm-shop`: the Spring Boot web application, the REST controllers, populators and mappers.
Changes usually touch more than one module. Check which module owns the behaviour before you edit.
The code is organised by layer more than by feature, so one feature is often spread over a controller, a facade, a
service, a repository and a populator. Find all of them before changing any.
The REST API is split between `/api/v1/private/...` (merchant administration, needs an admin token),
`/api/v1/auth/...` (logged-in customers) and `/api/v1/...` or `/api/v2/...` (public shop endpoints).
Do not assume that an endpoint behaves the same way for a guest and for a logged-in customer; check both paths.

### Build and test commands

- Use the Maven wrapper or the installed `mvn`. The sandbox has no network, so always pass `-o` (offline).
- Compile everything without running tests: `mvn -o -q -DskipTests test-compile`.
- Run the tests of one module: `mvn -o -pl sm-shop -am test`.
- Run one test class: `mvn -o -pl sm-shop -am -Dtest=ClassName -DfailIfNoTests=false test`.
- Do not run `mvn install`; it changes the shared local repository.
- JDK 21 is installed and `JAVA_HOME` is set. Do not change the Java version or the compiler settings.
- Read the first error in a Maven log, not the last. Later errors are usually a result of the first.
- A build that compiles is not a build that works. Run the tests that cover the code you changed.
- If a test was already failing before your change, say so in your summary; do not hide it and do not delete it.

### Code style

- Follow the style of the file you are editing: indentation, brace placement, naming, import order.
- Use meaningful names. A method name says what it does; a variable name says what it holds.
- Prefer small methods that do one thing. If a method needs a comment to explain each step, split it.
- Do not leave commented-out code, debugging output or unused imports in your change.
- Do not reformat lines you did not change. Large formatting diffs hide the real change from a reviewer.
- Keep public method signatures stable unless the ticket requires a change; if you change one, update every caller.
- Use the types the codebase already uses. Do not introduce a new library when an existing one does the job.
- Prefer constructor injection and the existing Spring conventions over new patterns.
- Put constants in the constants classes where the code base already keeps them.
- Write comments for why, not for what. The code already says what.

### Design guidance

- Put business rules in the service layer, not in controllers. Controllers translate HTTP to service calls and back.
- Keep controllers thin: validate input, call a facade or service, map the result, return the right status.
- Do not return entities directly from REST endpoints; use the response objects in `sm-shop-model`.
- Repositories talk to the database only; they do not hold business rules.
- When two code paths do nearly the same thing, make one call the other instead of copying the code.
- Prefer changing the code that is wrong over adding a workaround around it.
- Fix the cause of a bug, not only the symptom the report describes. A report names one symptom; there may be more.
- Look for the same mistake in sibling code (the other controller, the other service, the other entity).
- Think about what else holds a reference to the thing you change or delete: carts, orders, categories, images,
  inventory, customers, reviews.
- Think about what happens at the boundaries: empty, null, zero, one, many, the first, the last, a duplicate.

### Persistence and data

- The application uses Spring Data JPA with Hibernate. Entities are in `sm-core-model`.
- Be careful with lazy loading: accessing a lazy collection outside a transaction raises an exception.
- Be careful with cascade settings: a cascade that is too wide deletes more than you intended; too narrow leaves orphans.
- Deleting a row that other rows refer to fails or breaks those rows. Check the relationships first.
- Use transactions at the service level. A change that touches several tables must succeed or fail as a whole.
- Do not write raw SQL unless the codebase already does for the same purpose.
- Tests use an embedded database (H2). Do not rely on data that exists only in a developer's local database.
- If you add a column or table, check how the schema is created in this project before assuming it migrates itself.

### Error handling

- Return the HTTP status the ticket asks for. When it is silent, use the standard one: 404 for a missing resource,
  400 for bad input, 401 or 403 for authentication or permission failures, 409 for a conflict.
- Do not turn an expected condition (not found, invalid input) into a 500 server error.
- Do not swallow exceptions. Catch the narrowest type you can handle and let the rest propagate.
- Error messages should name the thing that went wrong and, where useful, what would be right.
- When a request is rejected, make sure nothing was saved or changed by it.
- Use the existing exception types and exception handlers rather than inventing new ones.

### Testing

- Add tests for the behaviour you changed, next to the existing tests of the same kind.
- A good test fails without your change and passes with it. Check that yours would fail on the original code.
- Test the behaviour the ticket describes, not the implementation details you happened to choose.
- Cover the normal case, the error cases the ticket lists, and at least one edge case.
- Keep tests independent: no test should rely on another test having run first.
- Do not disable, skip or delete an existing test to make the build pass.
- Do not weaken an assertion to make a test pass. If the test is wrong, say why in your summary.
- Some existing tests are skipped in this repository. A passing suite is therefore not proof that a feature works.
- Run the whole suite at least once before you finish, not only the tests you wrote.

### Security

- Never commit credentials, tokens or keys. Do not print them in logs.
- Check that a customer can only read and change their own data. Look for places where an id from the request is used
  without checking who owns it.
- Validate input at the boundary. Do not trust values from the request body, path or query string.
- Do not log personal data such as emails, addresses or payment details.
- Do not widen what an endpoint allows without being asked to.

### Working with the ticket

- A ticket may describe one symptom while the underlying problem is larger. Read the requirements as the full list.
- When a requirement is ambiguous, pick the reading that is consistent with the rest of the API and say which you chose.
- Do not ask questions; no one is available. Make a reasonable decision and record it in your summary.
- If you cannot do part of the ticket, say exactly which part and why, rather than implying it is done.
- Do not make unrelated improvements. A focused change is easier to review and less likely to break something.
- Keep notes of what you checked so your summary can be specific.

### Version control

- Do not rewrite history, create branches or push. Leave your change in the working tree.
- Do not commit generated files, build output (`target/`) or editor settings.
- Keep the change small enough to review in one sitting.
- Do not modify files under `.git`, the build configuration or the CI configuration unless the ticket needs it.

### Finishing

- Re-read the ticket one last time and tick off each requirement against your diff.
- Build and run the tests one last time after your final edit, not before it.
- In your summary, say what you changed, what you checked, and anything you could not do or are unsure of.
- Be accurate about what you ran. Say "I did not run X" rather than implying you did.
- If something is still failing, say so plainly.
