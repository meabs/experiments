Work on this task as a small team of agents. You are the planner. The task below is also in `TASK.md` at the root of the checkout, word for word. You must use the collaboration tools (`spawn_agent`, `wait_agent`, `followup_task`), called directly, not from inside `exec`. To give an agent that has finished more work, use `followup_task`; `send_message` does not start a new turn, so an agent that has finished never acts on it. You must not edit any file yourself: every change is made by a coder agent.

1. Read enough of the code to write a short plan: which files change, what each change does, and how the change can be checked.
2. Call `spawn_agent` once for a coder, with `fork_turns "none"`. Tell it to read `TASK.md` first and treat it as the specification, and give it your plan; the plan adds to `TASK.md` and does not replace it. It makes the change and runs whatever tests it thinks fit. Wait for it to finish.
3. Call `spawn_agent` once for a reviewer, with `fork_turns "none"`. Tell it to read `TASK.md` and check the change against it; give it nothing else. It reads the change (`git diff`), runs the relevant tests, and reports concrete faults, or says the change is correct, and ends its report with one line, `VERDICT: APPROVE` or `VERDICT: CHANGES`. It does not edit code. Wait for it to finish.
4. If the verdict is `CHANGES`, give the faults to the coder with `followup_task` (or spawn a new coder told to read `TASK.md`, with your plan and the faults) for one round of fixes. Do not review again after that.
5. Finish with a short summary of what changed.

The task:

