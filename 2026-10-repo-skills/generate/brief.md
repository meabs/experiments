You are working in a checkout of shopizer, a Java e-commerce platform (Maven, several modules; JDK 21 is installed and JAVA_HOME is set). Maven has no network access here: run it offline (`mvn -o`), with the dependencies already in `~/.m2`.

Other coding agents will be asked to fix bugs and add small features in this repository. They will see only the repository, your guidance and the request. Your job is to write the guidance that helps them make changes that are correct, and to check them properly before they say they are done.

Write:

1. `AGENTS.md` at the repository root. Keep it short. Say what the repository is, how it is laid out, the commands that matter, and which skill to use when.
2. Skills under `.agents/skills/<skill-name>/SKILL.md`. Each starts with YAML front matter holding `name` and `description` (the description says when to use the skill). Cover at least:
   - building the project and running its tests, including a single test or test class;
   - verifying a change against the running application. Either start the application, or write and run a test that starts it and calls the REST API the way a client would. Say which works here and exactly how;
   - making changes safely in this codebase: how a request flows through the layers, where to make a change, how errors become HTTP status codes, and how to find and check the other users of any shared code a change touches.

Rules:

- Base everything on this repository: its code, build files, configuration and existing tests.
- Run every command you recommend, here, and recommend only commands you have seen work. If something does not work here (for example, starting the application), say so in the guidance and give the route that does work.
- Do not change any other file. Anything you create or change outside `AGENTS.md` and `.agents/` is thrown away. Delete any scratch files and tests you write while working things out.

When you have finished, reply with a short list of the files you wrote.
