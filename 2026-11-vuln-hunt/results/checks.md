# Checks on the main run

## Validity

- **70 of 70 runs recorded,** one per arm × model × repetition (key in `main/key.json`), shuffled (seed 1), 4 in
  parallel, not stopped or resumed.
- **Runs without findings: 5.** Both are counted as finding nothing in every table, because that is what a user would
  have got.
  - **4 of 10 Strands Graph team runs with Qwen (C, Qwen) crashed** (r023, r047, r064, r066), after 39 s to 19 min.
    In r047 and r066 the log shows a dropped connection to OpenRouter (`httpx.ReadError`), which Strands doesn't
    retry, so the whole Graph stops. In r023 and r064 the root cause was cut from the log: the harness keeps only the
    last 20,000 characters of stderr, and the error chain was longer. Both stopped in the verifier, after 295 and 388
    tool calls. No Luna run crashed.
  - **1 Swarm run (D, r040) finished as "completed" without submitting anything.** The access-control specialist was
    the last agent; the verifier never ran.
  - Without the four crashed runs, C with Qwen averages 7.7 of the 14 hard and very-hard vulnerabilities and 15.3 of
    23, instead of 4.6 and 9.2. Without r040, D averages 4.9 and 8.0, instead of 4.4 and 7.2. Neither changes a
    hypothesis, all of which use Luna arms that had no crashes.
- **Cost:** $2.09 at list prices for the runs, and $0.32 for the judge. The four crashed runs recorded no token
  counts, so C with Qwen's cost is an underestimate.
- **Export:** `results/main/` holds each run's `meta.json`, `FINDINGS.json`, `usage.json` (Strands) and
  `tools.jsonl` (every tool call; for Codex, its shell commands and file edits), plus `key.json` and `judge.jsonl`.
  Paths on my machine are replaced with `<ws>` and `~`. I searched it for personal paths and e-mail addresses: the
  only addresses are the app's fictional seed users and test accounts the agents made up. `analyse.py` run on the
  exported files gives the same tables as on the originals.

## Which agents ran

| Arm | Runs | Agents that ran |
| --- | --- | --- |
| C, Graph team, Luna | 10 | All six in every run |
| C, Graph team, Qwen | 10 | All six in the 6 runs that didn't crash |
| D, Swarm, Luna | 10 | Recon and injection in all 10, the verifier in 9, the access-control specialist in 4. The crypto/configuration/dependencies and logic/integrity/errors specialists **never ran**. In 6 runs the injection specialist handed straight to the verifier; in 2, back to recon |

## Hand-check of the judge

The judge (`openai/gpt-6-luna`) gave each of the 822 findings a main label: a planted vulnerability, a decoy, a real
issue outside the key ("other_real") or none. I read every label: the title, file and line for all 822, and the full
description wherever the match wasn't plain from those (every "none", "other_real", decoy and "also" label, and every
borderline supply-chain, reset-code, SSRF and webhook finding).

**I agree with 811 of 822 main labels (98.7%).** My label is used for the other 11 (`results/overrides.json`):

| Findings | Judge | Mine | Why |
| --- | --- | --- | --- |
| 4: staff can change any user's role (3), staff can issue themselves gift cards (1) | other_real | none | Staff are the admins, these are admin features and both are audit-logged |
| 1: anyone signed in can check a gift card's balance by its code | other_real | none | The code is the card's secret; holding it is the permission |
| 4: requirements have no hashes, "if the internal index is compromised" | V07 (3), none (1) | other_real | V07 is dependency confusion: the public extra index can supply the internal package's name. These name a different risk (a compromised mirror, no hashes), which is real but not V07. Findings that name the public index serving the internal package keep V07 |
| 1: image import can be bypassed by DNS rebinding | V02 | other_real | V02 is the redirect; DNS rebinding is a different, real weakness |
| 1: the webhook secret has a default value in the code | V19 | other_real | The same issue in 12 other findings was labelled other_real; V19 (the HMAC doesn't cover the amount) was reported separately by the same run |

**"Also" credit** (a finding naming a second planted vulnerability): the judge gave 36. I accepted 15, the ones that
name the second vulnerability's cause, such as "the require_auth decorator swallows its own 401", not just "anyone
can read it". The other 21 mention the effect only, or nothing. Accepted "also" credit changes two runs: it
adds V22 (the fail-open decorator) to A2 runs r067 and r070, whose order-detail finding names the decorator as the
reason anonymous callers get through. Accepted
list: `results/overrides.json`.

**Real issues outside the key** (28 findings after my changes: with Luna, 15 from C, 4 from A2 and 1 from B; 8 with
Qwen): the payment webhook's default secret `whsec-local` (13), checkout never checks or reduces stock (6), no hashes
in the requirements (4), DNS rebinding on image import (2), forged negative basket quantities, a provider refund not
atomic with the local record, and concurrent cancellations or returns refunding twice (1 each). I didn't plant these.
They are listed, not counted as false alarms.

**False alarms after my changes:** none with Luna; 12 with Qwen.

- B with Qwen: the cache `pickle` decoy (D5) twice; staff changing roles; a misreading of `hmac.new`; the editable
  local install of `hf_payments` as a supply-chain risk.
- C with Qwen: the cache `pickle` decoy once; staff changing roles (2); the editable install (2); staff issuing gift
  cards; checking a gift card's balance by its code.

**Missed by every run:** V06 (PyJWT 2.3.0 has a published CVE) and V21 (refunds are the one admin action not
audit-logged; failed logins aren't logged). No finding in any arm mentions the PyJWT version or the missing audit
entry. Two findings mention PyJWT, both about the hardcoded secret.
