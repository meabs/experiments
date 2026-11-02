# A coding agent or a security specialist? Finding planted vulnerabilities

**Status: design.** Written 2026-11-01, before anything is built or run. Later changes go in the amendment log at the
end.

## Question

Developers already ask their general coding agent to "check this for security issues". Agent frameworks make it easy
to build a dedicated security reviewer instead, or a team of them. On the same web application, with known
vulnerabilities from easy to very hard to spot, and covering every OWASP Top 10:2025 category:

- does a security specialist agent find more of them than a general coding agent used as normal?
- does a swarm of specialists find more than one specialist?
- and what do the extra findings cost in false alarms, money and time?

This is authorised, defensive testing: the target is an application I write for this experiment. It runs only on
localhost inside the sandbox, with no network access, and the output is a list of findings to fix.

## The target

**`shopapi`:** a small Flask JSON API for the Hartley & Finch shop from
[need-an-agent](../2026-10-need-an-agent/), about 1,500 lines of Python with SQLite. It has accounts and login (JWT),
orders, refunds, gift cards, product reviews, image import from a URL, a payment-provider webhook and an admin area.
It is written to look like an ordinary small codebase: the vulnerabilities sit among working, tested code, and
nothing in comments or names hints at them.

**23 planted vulnerabilities,** at least two per OWASP Top 10:2025 category. The difficulty tier is my estimate,
fixed now. Results are reported per vulnerability as well, so a wrong estimate is visible.

| ID | OWASP 2025 | Tier | Vulnerability |
| --- | --- | --- | --- |
| V01 | A01 Broken Access Control | medium | `GET /orders/<id>` returns any customer's order (no ownership check) |
| V02 | A01 Broken Access Control | very hard | Image import checks the URL's host against an allowlist, then follows redirects, so it can be pointed at internal addresses (SSRF) |
| V03 | A01 Broken Access Control | hard | The admin check is in a `before_request` hook that matches the path exactly, so `/admin/refunds/` (trailing slash) skips it |
| V04 | A02 Security Misconfiguration | easy | The app starts with `debug=True` (interactive debugger) |
| V05 | A02 Security Misconfiguration | medium | CORS reflects any `Origin` with credentials allowed |
| V06 | A03 Software Supply Chain Failures | medium | `requirements.txt` pins a PyJWT version with a known algorithm-confusion vulnerability |
| V07 | A03 Software Supply Chain Failures | hard | An internal package name is installed through `--extra-index-url` from a public index, without hashes (dependency confusion) |
| V08 | A04 Cryptographic Failures | easy | A hardcoded `SECRET_KEY` used to sign tokens |
| V09 | A04 Cryptographic Failures | hard | Passwords hashed with unsalted SHA-256 |
| V10 | A04 Cryptographic Failures | very hard | Password-reset tokens from `random.random()`, compared with `==` |
| V11 | A05 Injection | easy | Product search builds SQL by string concatenation |
| V12 | A05 Injection | hard | Second-order SQL injection: a stored display name is later put into an admin report query |
| V13 | A05 Injection | medium | Stored XSS: review text rendered with `\|safe` in the HTML order page |
| V14 | A06 Insecure Design | very hard | Refund after a partial cancellation: the refund limit is the original total, so the cancelled amount can be refunded twice |
| V15 | A06 Insecure Design | hard | Gift-card redemption checks the balance and then deducts in two separate statements, so parallel requests overspend (race) |
| V16 | A07 Authentication Failures | medium | Login has no rate limit or lockout, and its error messages reveal whether an email exists |
| V17 | A07 Authentication Failures | hard | One route decodes the JWT with signature verification turned off |
| V18 | A08 Software or Data Integrity Failures | hard | The basket cookie is a base64 pickle, unpickled without a signature |
| V19 | A08 Software or Data Integrity Failures | very hard | The payment webhook's HMAC covers the order ID but not the amount, which is also trusted |
| V20 | A09 Security Logging & Alerting Failures | medium | The request logger writes full request bodies, including passwords and card numbers |
| V21 | A09 Security Logging & Alerting Failures | hard | Admin refunds are not audit-logged, though every other admin action is; failed logins aren't logged at all |
| V22 | A10 Mishandling of Exceptional Conditions | hard | The auth decorator catches any exception while checking the token and lets the request through (fails open) |
| V23 | A10 Mishandling of Exceptional Conditions | very hard | A payment-status timeout is treated as "paid" |

Tiers: easy 3, medium 6, hard 10, very hard 4. That puts most of the weight where the claim is about: whether
specialists find the hard ones.

**6 decoys:** code that looks risky but is safe, for counting false alarms:

- `ORDER BY` built from a whitelisted column name;
- `|safe` on HTML that `bleach` has already cleaned;
- `subprocess.run` with a fixed argument list and no shell;
- MD5 used only for an HTTP `ETag`;
- `pickle` loading a cache file that only the app writes, in a directory nobody else can write to;
- `DEBUG` read from an environment variable that defaults to off, in a second config file that isn't used.

**Answer key and proof tests.** Each vulnerability has a written description (file, function, what an attacker can
do) and a pytest test that demonstrates it against the local app. Each decoy has a test showing the safe behaviour.
The grader runs these tests to confirm the key; the agents never see the key or the tests (they are outside the
sandbox). A test file checks that the app works (the normal feature tests pass), so the agents see an ordinary,
working project.

## The three arms

All three get the same task text and the same output format:

> Review this repository for security vulnerabilities. Write each finding to `FINDINGS.json` as
> `{"file", "line", "category", "title", "description", "evidence"}`. Only report what you believe is a real
> vulnerability.

`category` is free text, so no arm is given the OWASP list.

| Arm | What it is | Model |
| --- | --- | --- |
| **A. Coding agent** | Codex CLI (0.164) used as normal: its own harness and default system prompt, one turn, in the bubblewrap sandbox used by earlier experiments. It can read files, run commands and start the app; no network | `gpt-5.6-luna`, medium effort, as in earlier experiments |
| **B. Specialist agent** | Built with [Strands Agents](https://strandsagents.com) (1.63). A security-reviewer system prompt with a checklist covering access control, configuration, dependencies, cryptography, injection, design and business logic, authentication, integrity, logging and error handling. It must give evidence for each finding. Tools: list files, read a file, search the code, and send HTTP requests to the app running on localhost (started by the harness) | `openai/gpt-5.6-luna` through OpenRouter, the same model as A |
| **C. Specialist swarm** | Strands' own `Swarm`: a recon agent maps the routes and data flows, then hands off to four specialists (injection and output; access control and authentication; cryptography, configuration and dependencies; business logic, integrity, error handling and logging), then a verifier checks each finding's evidence and writes `FINDINGS.json`. Same tools as B | the same |

The prompts are in [`prompts/`](prompts/): the task ([`task.md`](prompts/task.md)), B's checklist
([`specialist.md`](prompts/specialist.md)) and C's roles ([`swarm.md`](prompts/swarm.md)). They were committed with
this design, before the app was written. The checklist names general areas, following the OWASP 2025 categories, not
the planted bugs. But I wrote it after fixing the vulnerability list above, so some items ("data stored earlier and
used later", "admin functions protected on every path") are close to planted bugs. That favours B and C, and is
listed under threats.

**Replication:** B and C also run with `qwen/qwen3.7-flash`, a cheap model. Codex runs only with its own model, because
that is how it is used.

**Unavoidable differences, stated:**

- A has a general shell and can run anything in its sandbox; B and C have only the four tools.
- A's harness is OpenAI's, B and C's is Strands with LiteLLM.
- Token prices are the same model's list prices for A and OpenRouter's billed cost for B and C.

## Measures

Per run, from `FINDINGS.json`:

- **Recall:** the share of the 23 vulnerabilities found, overall, by tier and by OWASP category; higher is better. A
  finding counts as finding a vulnerability if it names the right place (file and function, or route) and the right
  problem. The category doesn't need to match OWASP's name.
- **False alarms:** findings that match no vulnerability. They are split into decoys flagged and other claims I judge
  wrong; lower is better. Real issues I didn't plant are counted separately and listed, not counted as false alarms.
- **Precision:** matched findings divided by all findings; higher is better.
- **Cost** (billed or list price), **tokens**, **wall time**, **model calls**, and for C the handoffs.

**Matching** is done by a judge model (`openai/gpt-6-luna`, JSON mode). It gets the answer key and one finding, and
returns the matching vulnerability ID, a decoy ID, or none. I check every match and every non-match by hand (about 25
runs × 15–30 findings), and report agreement. Where I disagree, my label is used and the disagreement is listed.

## Hypotheses

For the primary model (Luna):

- **H1:** the specialist (B) finds more hard and very-hard vulnerabilities than the coding agent (A).
- **H2:** the swarm (C) finds more hard and very-hard vulnerabilities than the specialist (B).
- **H3:** the specialist (B) has higher precision than the coding agent (A), because it is told to give evidence and
  can test against the running app.

**Tests:** the unit is the vulnerability. For H1 and H2, each of the 14 hard and very-hard vulnerabilities gets a
detection rate per arm over 5 runs. The paired differences get an exact sign-flip permutation test (one-sided) and a
bootstrap 95% interval (10,000, seed 1). H3 is a permutation test on per-run precision (one-sided). Holm correction
over H1 to H3. A non-significant result is reported as "no measurable difference". Everything else (easy and medium
tiers, per-category recall, cost, Qwen) is descriptive.

## Size

5 runs per arm: A × 5, B × 5, C × 5 with Luna, plus B × 5 and C × 5 with Qwen = **25 runs**. Expected cost: about
$0.20–0.50 a run for Codex and B, more for C. Under $10 in total; to be checked in the pilot.

## Pilot (before the main run)

One run of each arm with Luna, not part of the results:

- **Harness check:** each arm writes valid `FINDINGS.json`, the app starts, and no arm can see the key or tests.
- **Ceiling check:** if every arm finds nearly all the hard and very-hard vulnerabilities, I'll make them harder
  before the main run and record it in the amendment log. The same goes for the floor: if nothing finds any of them,
  I'll check they're findable at all.
- The pilot's findings and my changes are recorded here before the main run.

## Threats to validity

- **I wrote the app, the bugs and the specialist prompts,** knowing the bugs. The checklist follows OWASP's categories
  and is committed before the app, but it was written after the vulnerability list and some items are close to
  planted bugs. This favours B and C. A real specialist prompt would include similar items, but a gap in favour of
  B or C should be read with this in mind.
- **Planted bugs are not natural bugs.** They are deliberately placed in one small codebase, and real vulnerabilities
  are messier. The decoys and the "looks like an ordinary project" rule try to make it less of a treasure hunt.
- **Codex's model and harness can't be fully separated.** A uses the same model as B and C, so differences come from
  the harness and prompt, together.
- **The models may know common vulnerable-app patterns,** such as known vulnerable package versions.
- **25 runs is small.** The unit for the tests is the vulnerability (14 for H1/H2), so effects have to be large to show.

## Reproducing

To be filled in when the harness is built.

## Amendment log

- 2026-11-01: the user asked for "code with easy to very hard to detect vulnerabilities then use agents eg codex and
  then a agent framework using strands … using openrouter for the llm, do it head to head". They clarified: "Codex
  should be just a normal coding agent and harness, the intention is to test a coding agent vs a [specialist] agent",
  agreed to installing Strands and to the swarm arm ("Yes to both"), and asked: "can we cover oswap in it". Design
  written to cover all ten OWASP Top 10:2025 categories.
- 2026-11-01, during the build, before the pilot (no run had been made):
  - **Tier counts corrected:** the table above gives easy 3, medium 6, **hard 9, very hard 5** (I miscounted them as
    10 and 4 in the text). The table, and the 14 hard and very-hard vulnerabilities used for H1 and H2, are unchanged.
  - **V06 pins PyJWT 2.3.0** (CVE-2022-29217, algorithm confusion, fixed in 2.4.0). PyJWT 1.x doesn't run on the
    machine's Python 3.14.
  - **The app is about 1,200 lines,** not 1,500.
  - **Codex's sandbox has network access,** because Codex reaches its model over it; web search is disabled. B and C
    can only reach the local app through their HTTP tool.
  - **B and C use Strands' Responses-API model** (`OpenAIResponsesModel`) on OpenRouter, with reasoning effort
    medium, like Codex. Through the Chat Completions model, Strands drops the model's reasoning between turns (it
    warned about this in a smoke test), which Codex doesn't.
  - **The matching judge returns one more label,** "other_real", for real issues outside the key, so they aren't
    counted as false alarms ([`src/judge.py`](src/judge.py)).
- 2026-11-01, during the pilot, before the main run: **a fourth arm, A2 (Codex + checklist).** The user asked: "Is it
  worth having an arm where the codex has the same kniwldge as strands", and said "Yes" to the proposal below.
  - **A2** is Codex, set up exactly as A. Its prompt is B's system prompt (the checklist in
    [`prompts/specialist.md`](prompts/specialist.md) plus the same line saying where the running app is), followed by
    the same task. The harness starts a copy of the app for A2 as it does for B and C. The only wording difference is
    how to reach it: "with curl" for Codex, "with the http_request tool" for Strands.
  - **New hypothesis H4:** A2 finds more hard and very-hard vulnerabilities than A (the checklist's effect inside
    the same harness). Same test, one-sided, and Holm now covers H1 to H4.
  - **A2 against B** (the same instructions and model, Codex's harness against Strands') is reported as a
    difference with a bootstrap interval, without a test.
  - **Size:** 30 runs (A2 × 5 added). A2 gets one pilot run.
- 2026-11-02, after the pilot of A, A2 and B and two failed pilots of C, before the main run. **Arm C becomes a
  Strands Graph; the Swarm becomes arm D, reported descriptively.** The user chose this ("Graph + Swarm") from three
  options I offered.
  - **What went wrong with Strands' Swarm** (arm C as designed):
    - Run 1: the recon agent called `list_files` in a loop for 315 model calls and never handed off. It ended on a
      connection error, with no findings.
    - Then, in tests: recon handed off to all five colleagues in one parallel step. Agents kept working after
      handing off, because a Strands handoff only records the next agent and the last one wins. The order was
      ignored: specialists went straight to the verifier, and the verifier sent work back to recon. Two of the four
      specialists never ran. The verifier submitted three times, the last time an empty list.
    - Fixes tried: one tool call per step (`parallel_tool_calls: false`, which OpenRouter's Responses route seemed to
      ignore); a hook that ends an agent's turn after its first handoff and refuses a second (as OpenAI's Swarm
      does); roles naming the next agent. Handoffs then happened one at a time, but the order still wasn't followed.
  - **C, specialist team (Strands Graph,
    [`prompts/team.md`](prompts/team.md)):** the same six roles. Recon runs first, the four specialists run in
    parallel with recon's map, and the verifier runs once all four have finished, with their findings. The order is
    fixed in code. A test run completed with 17 findings in about 3 minutes.
  - **D, specialist swarm (Strands Swarm, [`prompts/swarm.md`](prompts/swarm.md)):** kept with the fixes above.
    Roles name the next agent, and handoffs are one per turn. D has no hypothesis; it is reported descriptively,
    including how often a run fails or skips specialists.
  - **All Strands arms (B, C, D):**
    - `submit_findings` accepts only the first call (this stopped D's empty overwrite).
    - The conversation keeps the first message and a 300-message window (Strands' default is 40). This was added
      while chasing the loop. It wasn't the cause, but it stops a long review from losing its task.
    - Every tool call is logged.
  - **H2 now reads:** the specialist team (C, Graph) finds more hard and very-hard vulnerabilities than the specialist
    (B).
  - **Size:** A, A2, B, C, D × 5 with Luna, plus B and C × 5 with Qwen = **35 runs**.
- 2026-11-02, after the pilot, before the main run:
  - **Pilot** (one run per arm with Luna; not part of the results). Planted vulnerabilities found (of 23), hard and
    very hard found (of 14), findings, time and cost at list prices:

    | Arm | Found | Hard + very hard | Findings | Time | Cost |
    | --- | --- | --- | --- | --- | --- |
    | A, Codex | 12 | 8 | 12 | 48 s | $0.018 |
    | A2, Codex + checklist | 12 | 7 | 12 | 59 s | $0.019 |
    | B, Strands specialist | 12 | 8 | 12 | 66 s | $0.013 |
    | C, Strands team (Graph) | 17 | 11 | 18 | 119 s | $0.049 |
    | D, Strands swarm | 8 | 5 | 8 | 225 s | $0.034 (2 of 4 specialists skipped) |

    - **Ceiling:** no arm found more than 11 of the 14 hard and very-hard vulnerabilities, so none were changed.
    - **No false alarms in the pilot:** every finding matched a planted vulnerability, and no decoy was flagged. H3
      (precision) may therefore have little to measure; it stays as designed.
    - **Judge:** I checked all 74 pilot labels and agreed with every main match. The judge also gave "also" credit
      in 3 findings. These count only if the finding names the second vulnerability's cause; it made no difference
      in the pilot, because those runs reported the second vulnerability separately.
  - **10 runs per arm instead of 5,** because runs cost 1 to 5 cents. This was decided from the pilot's cost, not its
    results. A, A2, B, C, D × 10 with Luna, plus B and C × 10 with Qwen = **70 runs**, under $5.
- 2026-11-02, after the main run (nothing in the arms, measures or hypotheses changed):
  - **Runs without findings count as finding nothing.** The design didn't say how to treat a crashed run. Four of
    the ten Graph team runs with Qwen crashed, and one Swarm run ended without submitting. I counted them as zero,
    because that is what a user would get, and report the numbers without them in
    [`results/checks.md`](results/checks.md). No Luna run in a hypothesis crashed.
  - **Scripts written or committed after the design push:** `src/batch.py` (the main-run driver) was written before
    the main run but not committed with the design. `src/analyse.py` (tables and tests, as described above),
    `src/export.py` and `results/overrides.json` (my hand labels) were written during and after the run. The run log
    showed each run's number of findings while I wrote `analyse.py`, not which vulnerabilities they matched.
