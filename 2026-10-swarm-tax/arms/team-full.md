Work on this task as a team, using subagents. You are the planner.

1. Read enough of the code to write a plan: which files change, what each change does, and how the change can be checked. If the work splits cleanly into independent parts, divide it into at most two parts. Do not edit any code yourself.
2. Spawn one coder subagent per part (at most two), each with `fork_turns "none"`. Give each the task text, your plan, and its part. Each makes its part of the change and runs whatever tests it thinks fit.
3. When the coders have finished, spawn a reviewer subagent with `fork_turns "none"`. Give it only the task text. It reads the whole change (`git diff`), runs the relevant tests, and reports concrete faults, or says the change is correct. It does not edit code.
4. If the reviewer reports faults, have a coder fix them, then spawn a new reviewer the same way. Repeat for at most three rounds of review in total.
5. Finish with a short summary of what changed.

The task:

