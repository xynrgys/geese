# Architectural Rules & Conventions

Welcome to the automated task environment! You are an unattended one-shot agent.
You must complete your given task without waiting for additional user input.
Do not output "I am ready" or prompt the user for follow-ups.

## Code Conventions
1. **Naming**: Use descriptive camelCase for variables, PascalCase for classes and interfaces.
2. **Logic**: Refactor logic clearly. For example, if adding JWT authentication, use industry-standard libraries (like `jsonwebtoken` or `pyjwt`) and avoid reinventing the wheel.
3. **Tests**: When you write or refactor code, verify that the existing tests pass. Do not remove tests unless explicitly asked to do so. If the code requires an updated test, please update it.

## Execution Rules
- Always use the tools available (e.g. `npm run lint` or `pytest`) to verify your code before completing the task.
- If you see a linter or test failure, you must fix it immediately.
- Do not make changes outside the scope of the immediate task.
- When done, exit successfully. You will be invoked by a deterministic state machine, so returning a successful exit code after fixing the bug is required.