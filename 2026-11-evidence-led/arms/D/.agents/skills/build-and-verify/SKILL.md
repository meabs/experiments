---
name: build-and-verify
description: Use before you finish: build the project, run the tests that cover your change and the rest of the suite, and fix failures.
---

# Build and verify

1. Find how the project builds and runs its tests (README, build files, wrapper scripts). Prefer the project's own
   wrapper and an offline build if dependencies are already present.
2. Build the whole project. Fix compile errors before anything else.
3. Run the tests that cover your change, then the whole test suite.
4. If a test fails:
   - if your change caused it, fix your change;
   - if it failed before your change, leave it and say so in your summary.
   Never disable, delete or weaken a test to make a run pass.
5. Read the test output, not just the exit code: how many tests ran, failed, errored and were skipped.
6. In your summary, say which commands you ran and what they reported.
