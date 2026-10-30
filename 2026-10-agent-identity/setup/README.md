# What was installed and configured

- **Keycloak 26.8.1** (released 2026-10-13), the server distribution, not a container (Docker is not installed on this machine).
  - Downloaded from `https://github.com/keycloak/keycloak/releases/download/26.8.1/keycloak-26.8.1.tar.gz`. SHA-1 `f55701155746ed88e12b3e670d5fa03589e3013e`, matching the published `.sha1`.
  - Unpacked to `~/code/benchmark/local-setup/keycloak/keycloak-26.8.1`. Nothing was installed system-wide.
- **Java:** the existing OpenJDK 21.0.12.1 (Keycloak 26 needs Java 21).
- **Python packages**, fetched per run by `uv run --with`: httpx, pyjwt, cryptography.
- **Codex CLI 0.157.0:** the existing hosted install, `~/code/benchmark/local-setup/codex-pkg`.

## Starting Keycloak

```bash
cd ~/code/benchmark/local-setup/keycloak/keycloak-26.8.1
KC_BOOTSTRAP_ADMIN_USERNAME=admin KC_BOOTSTRAP_ADMIN_PASSWORD=admin-local-only \
  bin/kc.sh start-dev --http-port=8180 --http-host=127.0.0.1 \
  --features=token-exchange-delegation,parameterized-scopes,resource-indicators
```

The flags:

- **Dev mode:** HTTP, in-memory H2 database, listening on localhost only. The admin password is a local throwaway.
- `token-exchange-delegation` (**preview** in 26.8.1, off by default) adds RFC 8693 delegation: `may_act` in the user's token, `act` in the exchanged one. It needs `parameterized-scopes` (preview).
- `resource-indicators` (**experimental**) was switched on to check its status and is not used by the setups.
- Standard token exchange (v2) and DPoP are supported features, on by default.

## Then

```bash
cd ~/code/experiments/2026-10-agent-identity
uv run --with httpx python3 -I src/realm.py          # builds the "acme" realm; writes setup/local-secrets.json (git-ignored)
uv run --with httpx --with pyjwt --with cryptography python3 -I src/services.py results/audit.jsonl &
```

The realm builder turns on these settings for setup 4. None of them is on by default:

- **Admin permissions (FGAP v2)** on the realm, plus a permission saying the `assistant` client may delegate for all users. Without it, Keycloak silently drops the delegation scope.
- **Consent required** on the `assistant` client. Delegation always asks for consent, and Keycloak does not store it, so users approve again at every sign-in.
- **The `exchange-downscope-only` client policy**, using the `downscope-assertion-grant-enforcer` executor. Without it, token exchange can add scopes the original token never had (see the chain scenario).
