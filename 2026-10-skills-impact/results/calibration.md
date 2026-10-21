# Calibration (2026-10-21)

The `none` arm only, 3 runs per agent per task version. Rule from the design: a change task is kept if the control passes 1 or 2 of 3 on at least one agent. These runs are not part of the results.

| Task version | Codex | Cursor | Tokens per run, Codex / Cursor (median) | Decision |
| --- | --- | --- | --- | --- |
| BUG v1: special-price slip in `ProductPriceUtils` | 3/3 | 3/3 | 479k / 528k | ceiling: made harder |
| BUG v2: special end date saved as start date in `PersistableProductAvailabilityMapper` | 3/3 | 3/3 | 593k / 125k | ceiling: made harder |
| BUG v3: both slips together (one symptom, two causes) | 2/3 | 3/3 | 1.09M / 194k | **kept** |
| FEAT v1: cart line limit of 99 | 3/3 | 3/3 | 2.84M / 573k | ceiling: made harder |
| FEAT v2: limit from merchant configuration, default 99 | 3/3 | 3/3 | 3.64M / 810k | kept for cost and process only (user decision) |
| CROSS: manufacturer website end to end | 1/3 | 3/3 | 2.47M / 342k | **kept** |

How the failures happened (every one is a genuine defect, checked by reading the diff):

- CROSS, Codex runs 2 and 3: validation added as `@Pattern` on the API model, plus a handler for validation errors. Shopizer has no bean-validation provider on its classpath, so the annotation never runs, and an invalid website is stored (201). Both runs reported `passed`, and neither tried an invalid website against the running API.
- BUG v3, Codex run 2: both causes fixed correctly, but the agent added a unit test that fails, which leaves the build red. It reported `passed`.

Checker defects found and fixed during calibration:

1. BUG v2 runs at first all failed, because `verify.sh` copied the new API-level hidden test into `sm-core`, where the v1 unit test lived, and it did not compile there. After the fix, the 6 runs were re-verified from their saved diffs with `scripts/reverify.sh`: 6/6 passed.
2. Maven stopped at the first failing module, so a red `sm-core` hid the `sm-shop` hidden test. The verifier now runs every module with `-Dmaven.test.failure.ignore=true`, and `scripts/summarize.py` reads the surefire reports and records `hidden_pass`, `other_failures` and the failing suites in `verify-summary.json`. Pass means: the reactor ran, every hidden test passed, and no other test failed, including tests the agent added. A change that leaves the build red would not merge.
3. The FEAT v2 runs started while the verifier was being edited, so all 6 were re-verified with the final script: 6/6 passed.

Note on the claim line: Cursor (Grok 4.7 low) often answers `not-run` even when it ran Maven. Codex always says `passed`, including in all 3 of its failed runs.
