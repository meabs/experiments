# Local-model setup for AgentTrialRig (GMKtec NucBox EVO-X2, Ubuntu)

Everything needed to rerun the Codex experiments against a local open-weight model instead of `gpt-5.6-luna`.
Status: set-up complete and checked (model server, Codex, toolchain, isolation, localization, smoke tests). Used by
`~/code/experiments/2026-10-test-skill-local`, which keeps a copy of these scripts in `setup/`.

## Machine
- GMKtec NucBox EVO-X2, Ubuntu 26.04.1 LTS, kernel 7.0.0-38-generic
- AMD Ryzen AI Max+ 395 (16C/32T); 64 GB unified memory, BIOS split 32 GB GPU (VRAM carve-out) / 30 GiB OS
- GPU: Radeon 8060S iGPU, gfx1151, ROCm at /opt/rocm. No NVIDIA.

## Model server
- **Ollama 0.40.5**, the tarball install at `/usr/local/bin/ollama`, run as `ollama.service` (ROCm 7.2 backend).
- The snap Ollama (0.40.2) is **disabled**: snap confinement kept it on CPU (`size_vram: 0`). Undo with `sudo snap start --enable ollama`.
- `sudo-step1.sh` disables the snap, writes the override and installs the JDK and Maven. `/etc/systemd/system/ollama.service.d/override.conf` contains:
  ```
  OLLAMA_MODELS=/var/snap/ollama/common/models   # reused store, chowned to ollama:ollama
  OLLAMA_CONTEXT_LENGTH=65536
  OLLAMA_FLASH_ATTENTION=1
  OLLAMA_KEEP_ALIVE=30m
  OLLAMA_NUM_PARALLEL=1
  ```
- **Model: `qwen3.8:27b`**, i.e. `qwen3.8:27b-q4_K_M`, family qwen35, 27.3B parameters, **Q4_K_M** GGUF, Ollama digest `aaee06c39dcf…`.
  Native context is 262k; served at **65,536**. The whole model is in VRAM (16.8 GB).
- Measured speed: prefill **344 tok/s** on a 14k-token prompt; generation **34 tok/s** on a short context and **15 tok/s** at 14k.
  The CPU-only snap managed 30 tok/s prefill.

## Codex
- **Codex CLI 0.157.0**, the version pinned by the experiments. Installed with `npm install -g --prefix local-setup/codex-pkg @openai/codex@0.157.0`.
  Run it as `local-setup/codex-pkg/bin/codex`. It is not on the global PATH, and `~/.codex` is untouched.
- Throwaway `CODEX_HOME=local-setup/codex-home`. Its `config.toml` defines `model_providers.ollama-local`:
  `base_url = http://127.0.0.1:11434/v1`, `wire_api = "responses"` (the only value 0.157 accepts), `env_key = OLLAMA_API_KEY` (any value works).
- **Model catalog** (`model_catalog_json = codex-home/catalog.json`): without one, Codex logs `Model metadata … not found` and uses fallback tools.
  `make_catalog.py` builds the entry by cloning `gpt-5.6-luna`'s entry from the 0.157.0 `models.json` (copy in `codex-models-0.157.0.json`),
  so prompts, truncation and shell tool match luna. The entry is renamed to `qwen3.8:27b`, with context 65,536, auto-compact at 56,000, text-only input, no websockets and no service tiers. Three more changes were needed for Ollama:
  1. `use_responses_lite = false`. Ollama rejects the `additional_tools` input item (HTTP 400).
  2. `tool_mode = null` instead of `code_mode_only`. The code-mode `exec` tool is a custom tool; Ollama returns it as a plain `function_call`, Codex never answers it, and every call aborted.
  3. `apply_patch_tool_type = null` instead of `freeform`, for the same reason: patch calls got no output. (`function` isn't a valid value in 0.157.)
     The agent edits files through the shell, where `apply_patch` still works as a command.
  These three are **real differences from the luna runs** and must be reported as such.
  Command used: `python3 -I make_catalog.py codex-models-0.157.0.json codex-home/catalog.json use_responses_lite=false apply_patch_tool_type=null tool_mode=null`
  (catalog.json sha256 `344a16c0…88ccea`).
- Tool-calling check (`toolcheck.sh <dir>`): read calc.py, fix it, run python. Passed 3 out of 3 runs in 35–43 s, using 30–37k input tokens. Verified from the
  session rollout (every call has an output) and by re-running `calc.add(2,3)` myself, not from the agent's report.

## Toolchain
- openjdk-21-jdk-headless 21.0.12.1+1-1~26.04.4 (`JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64`), maven 3.9.12-1 (apt)
- git 2.53.0, uv 0.13.1, Python 3.14.4, bubblewrap 0.11.1 (already present)
- shopizer at `6a4a0a6` in `~/code/benchmark/skills-impact-work/shopizer`, which is the toml's `source`. Never modified.
- `~/.m2` was warmed by `mvn -B -Dmaven.test.failure.ignore=true clean test` on that clone. These are the same goals `verify.sh` runs offline. No `install` was run. Log: `warm-m2.log`.
- Repositories: `~/code/benchmark/AgentTrialRig`, `~/code/experiments` (as expected by `localize.sh`).

## Isolation (replaces the rig's macOS-only `isolate`)
- `codex-bwrap.sh` is the agent `command` in every localized toml (`isolate = []`). bubblewrap 0.11.1:
  read-only `/`; empty tmpfs on `/home`, `/tmp` and `/run/user`; bound back in are the run's clone (read-write), the Codex
  binary (read-only), a fresh per-run `~/.codex` (kept in `<out>/agent-homes/<run id>/`, not exported), and
  `~/.m2/repository` as an overlay with a tmpfs upper layer (agent writes, e.g. `mvn install`, vanish).
  `--clearenv`, then only HOME, USER, CODEX_HOME, JAVA_HOME, PATH, LANG, TERM, OLLAMA_API_KEY. The network is shared (needed for 127.0.0.1:11434).
- `isolation-test.sh <dir> [--codex]`: 17 probes from inside the sandbox plus the real agent told to print the hidden tests.
  It passed every check, with the out folder under `~/code/benchmark/trials`. If it is run from a folder under `/tmp`, the `/tmp`
  probe fails, because the clone is bound back inside `/tmp`. Log: `isolation-test.log`.
- `CODEX_SEED=<dir>` (arm F, gate): `<dir>/.codex` (hooks.json and gate scripts) is copied into each run's fresh home.
  Built by `localize-linux.sh` as `gate-seed/`, with `relevance.sh` using the Linux JDK.
- `CODEX_PROFILE=hosted` (calibration only): the per-run home gets the real `~/.codex/auth.json` and an empty config,
  as TSK's clean home, so Codex uses OpenAI and luna's built-in catalog.

## Localization
- `localize-linux.sh [experiment dir]` runs the experiment's own `localize.sh` and then rewrites each `trial*.local.toml`.
  The agent runs through the wrapper with `--model qwen3.8:27b` and the original `args`; `parallel = 1`; the timeouts
  stay as designed. It also writes `scripts/verify.local.sh` and `scripts/relevance.local.sh` (Linux JDK in place of
  `/opt/homebrew/opt/openjdk@21`).
- The master `codex-home/config.toml` must not collect `[projects."…"]` trust entries; Codex adds them when run
  directly in a folder. They were removed after the tool checks.

## Power
- `powerlog.sh <csv>`: APU package power (hwmon `PPT`, CPU and GPU together; Strix Halo has no GPU-only sensor), once a second.
  The smoke run averaged 84 W.

## Smoke tests (ADDR, arm A; not results)
- Run 1, 60-minute limit: timed out. The edit was correct (2/2 hidden tests, existing suite 0 failures). 114 turns,
  about 2.7M tokens, 84 Wh. The checksum of `~/.m2/repository/com/shopizer` was unchanged afterwards.
- Run 2, no limit (`trial-smoke.local.toml`, timeout 86400): result in the experiment's amendment log.
