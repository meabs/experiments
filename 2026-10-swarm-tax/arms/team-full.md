Work on this task as a team of agents. You are the planner. You must use the collaboration tools (`spawn_agent`, `wait_agent`, `followup_task`), called directly, not from inside `exec`. To give an agent that has finished more work, use `followup_task`; `send_message` does not start a new turn, so an agent that has finished never acts on it. You must not edit any file yourself: every change is made by a coder agent.

1. Read enough of the code to write a plan: which files change, what each change does, and how the change can be checked. If the work splits cleanly into independent parts, divide it into at most two parts.
2. Call `spawn_agent` for one coder per part (at most two), each with `fork_turns "none"`. Give each the task text, your plan, and its part. Each makes its part of the change and runs whatever tests it thinks fit. Wait for them to finish.
3. Call `spawn_agent` for a reviewer, with `fork_turns "none"`. Give it only the task text. It reads the whole change (`git diff`), runs the relevant tests, and reports concrete faults, or says the change is correct, and ends its report with one line, `VERDICT: APPROVE` or `VERDICT: CHANGES`. It does not edit code. Wait for it to finish.
4. If the verdict is `CHANGES`, have a coder fix the faults (`followup_task` to an existing coder, or a new coder), then spawn a new reviewer the same way. Repeat for at most three rounds of review in total.
5. Finish with a short summary of what changed.

The task:

