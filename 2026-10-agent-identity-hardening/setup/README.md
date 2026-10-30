# What was installed and configured

Nothing new was installed. This follow-up reuses the first test's Keycloak 26.8.1 server distribution (see [../../2026-10-agent-identity/setup/README.md](../../2026-10-agent-identity/setup/README.md)), Java 21, Codex CLI 0.157.0, and Python packages fetched by `uv run --with` (httpx, pyjwt, cryptography).

## Starting Keycloak

The command is the first test's, plus the CIBA option, which points Keycloak's "authentication channel" at the mock phone (`src/phone.py`, port 8400):

```bash
cd ~/code/benchmark/local-setup/keycloak/keycloak-26.8.1
KC_BOOTSTRAP_ADMIN_USERNAME=admin KC_BOOTSTRAP_ADMIN_PASSWORD=admin-local-only \
  bin/kc.sh start-dev --http-port=8180 --http-host=127.0.0.1 \
  --features=token-exchange-delegation,parameterized-scopes,resource-indicators \
  --spi-ciba-auth-channel--ciba-http-auth-channel--http-authentication-channel-uri=http://127.0.0.1:8400/notify
```

## Then

```bash
cd ~/code/experiments/2026-10-agent-identity-hardening
uv run --with httpx --with cryptography python3 -I src/realm.py      # realm, client keys -> setup/local-secrets.json (git-ignored)
uv run --with httpx python3 -I src/phone.py results/phone.jsonl &
uv run --with httpx --with pyjwt --with cryptography python3 -I src/services.py $PWD/results/audit.jsonl &
```

The realm builder adds the following to the first test's setup 4 configuration:

- **`private_key_jwt` on the `assistant` client.**
  - `clientAuthenticatorType=client-jwt`.
  - The public key is registered in `jwks.string`, signing algorithm ES256.
- **A realm CIBA policy:**
  - poll mode;
  - 120 s expiry;
  - `login_hint` names the user.
- **The `approvals` client:**
  - `oidc.ciba.grant.enabled=true`;
  - `private_key_jwt`;
  - DPoP-bound tokens;
  - optional scope `expenses.approve.high`.
- **`expenses.approve.high` as a parameterised scope.**
  - Attributes `is.parameterized.scope=true`, `parameterized.scope.type=custom` and `parameterized.scope.regexp=EXP-[0-9]+`.
  - These attribute names come from the 26.8.1 server jar. The older `is.dynamic.scope` attributes are deprecated and were rejected.

## Keycloak details found while setting up

- **Requested scopes are checked against the scope's settings.** CIBA first refused `expenses.approve.high:EXP-9` with "Invalid scopes" until the parameterised-scope attributes above were set.
- **The CIBA `binding_message` is limited** to 50 characters, with no spaces: "the binding_message value has to be max 50 characters in length and must contain only basic plain-text characters without spaces".
