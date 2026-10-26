Work on this task as a small team, using subagents. You are the planner.

1. Read enough of the code to write a short plan: which files change, what each change does, and how the change can be checked. Do not edit any code yourself.
2. Spawn one coder subagent with `fork_turns "none"`. Give it the task text and your plan. It makes the change and runs whatever tests it thinks fit.
3. When the coder has finished, spawn one reviewer subagent with `fork_turns "none"`. Give it only the task text. It reads the change (`git diff`), runs the relevant tests, and reports concrete faults, or says the change is correct. It does not edit code.
4. If the reviewer reports faults, send them to the coder (or spawn a new coder with the task, your plan and the faults) for one round of fixes. Do not review again after that.
5. Finish with a short summary of what changed.

The task:

