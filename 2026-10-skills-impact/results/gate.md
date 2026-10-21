# Isolation gate (2026-10-21)

One run per arm and agent of `gate.toml`: "list every agent skill available to you; list any whose full instructions are already loaded". Built-in skills are the ones each CLI ships with.

| Arm | Codex | Cursor | Loaded at start |
| --- | --- | --- | --- |
| `none` | built-ins only | built-ins only | none |
| `placebo` | + careful-engineering | + careful-engineering | none |
| `superpowers` | + 15 skills | + 15 skills | using-superpowers (via AGENTS.md) |
| `pocock` | + 11 skills | + 11 skills | none |
| `pstack` | not run | + poteto-mode, setup-pstack | poteto-mode (via the `/poteto-mode` prefix) |

Built-ins: Codex `imagegen, openai-docs, plugin-creator, skill-creator, skill-installer`. Cursor `autopilot, create-hook, create-rule, create-skill, loop, new-repo, origin, review-bugbot, review-security, sdk, share, split-to-prs, statusline, update-cli-config`.

`pocock` ships 27 skills, of which 16 set `disable-model-invocation: true`, so the agent is shown 11. `pstack` ships 56, of which 55 are user-invoked only: `poteto-mode` reaches the rest by file path. Both are the packs as published.

The first gate run failed: no treatment arm saw its skills. Cause: AgentTrialRig's `isolate` denied the results folder, which contains each run's work folder, and both CLIs silently skip project skills when they cannot read the metadata of the work folder's ancestors. The rig now allows metadata (not contents) on those ancestors, with a test. The gate above is the second run.
