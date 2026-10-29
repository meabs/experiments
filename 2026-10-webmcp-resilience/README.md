# WebMCP Resilience: parked experiment, and a demo

**Status: the experiment is parked. The demo is done: see [demo/README.md](demo/README.md).**

## The experiment (parked)

The plan was to test whether a coding agent fixes a reported timing bug in a WebMCP page more often with
[WebMCP Resilience](https://github.com/meabs/WebMCPResilience) available than without it.

- **Built:**
  - six small WebMCP apps, each with one planted timing bug, spread over several files with decoys (`apps/`);
  - vague, user-style bug reports (`tasks/`);
  - hidden Playwright tests (`hidden/`);
  - reference fixes (`reference/`);
  - 12 plausible but wrong fixes (`wrong-fixes/`);
  - the agent setups, with and without the tool (`arms/`).
  The grader validates: originals and wrong fixes fail, references pass.
- **Why it's parked:** in the pilot, gpt-5.6-luna fixed 5 of the 6 bugs without the tool, so there was little room for
  the tool to help. A local model (qwen3.8:27b) could do the tasks but took about 22 minutes a run. A smaller one
  (qwen3:8b) couldn't drive the agent at all. The pilot runs aren't published.

## The demo

Instead of asking whether an agent needs the tool, the demo asks whether the tool catches what an ordinary check
misses. It runs WebMCP Resilience and an ordinary check against 31 versions of the six apps: buggy originals, correct
fixes, wrong fixes and real agent fixes. See [demo/README.md](demo/README.md).
