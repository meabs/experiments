# Gate (2026-10-21)

One run per arm and agent of `gate.toml`, asking the agent to list its skills and any already loaded. `caveman` sets `disable-model-invocation: true`, so it starts only when invoked. Two invocation prefixes were tried: `slash` is `/caveman` and `dollar` is `$caveman`.

| Arm | Codex | Cursor |
| --- | --- | --- |
| none | listed: no; loaded: none | listed: no; loaded: none |
| slash | listed: yes; loaded: none | listed: yes; loaded: caveman |
| dollar | listed: yes; loaded: caveman | listed: no; loaded: none |

Result: Codex loads caveman with `$caveman` and Cursor with `/caveman`; neither loads it with the other agent's syntax. The measured `caveman` arm therefore uses each agent's own prefix (`trial-codex.toml`, `trial-cursor.toml`). `none` sees only the built-in skills, as in skills-impact.
