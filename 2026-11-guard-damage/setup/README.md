# setup

- `dot-agenttrail/`: the AgentTrail Guard 0.4.21 hook bundle (`@agenttrail/guard`, Apache-2.0, https://www.agenttrail.sh/agenttrail-guard), copied unmodified from 2026-11-agenttrail-guard/setup/guard-home. Default configuration; `guardrails.json` is empty (no custom rules).
- `dot-codex/`: Codex's `hooks.json` and a `config.toml` holding the two `/hooks` approval hashes for that bundle. The hashes contain the path `/home/garry/.codex/hooks.json`, so runs must keep that layout. No credentials are in this folder.
