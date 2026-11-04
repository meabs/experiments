# accounts-service

- Build and run the tests with `mvn -o -q test` (offline: every dependency is already in the local Maven repository).
  Do not run `mvn install`.
- README.md describes the packages, the security model and the API conventions.
- `okf/` is this repository's knowledge bundle (Open Knowledge Format): the key facts and pitfalls, the external
  systems and how they behave, and the business processes the service supports. Start at `okf/index.md`.

`okf/` is maintained by hand and can be out of date. Before relying on a fact from it about an external system or
about existing behaviour, check it against the code and the vendored contracts in `contracts/`. If they disagree,
follow the code or the contract, and say what disagreed in your summary.
