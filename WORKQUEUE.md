# Overnight Build Queue

Execute the two plans below **task by task, test-driven**, one commit per task.

## Contract (non-negotiable)
- TDD: write the failing test, watch it fail, implement, watch it pass, commit. Follow each plan's steps exactly.
- One PR per skill, off `main`. **Never merge to main. Never push to main directly. Never change repo visibility (stays private). Never publish anywhere.**
- Treat all generated output as untrusted; verify by running the tests (`pytest skills/ -q`), not by trusting prose.
- Keep every artifact clean and handoff-ready (as if onboarding a human dev tomorrow).
- If a step is genuinely blocked, stop that skill, leave a note in the PR description, and continue the other skill. Do not improvise around the plan.

## Queue (in order)
1. `docs/plans/2026-10-11-audit-workplan-generator.md` — finish the 5 gaps (feasibility light, scope reduction, Monday top-3, framework templates, cost ranges). Branch `build/audit-workplan-generator`. Expected end state: `pytest skills/audit-workplan-generator/tests/ -q` = 16 passed.
2. `docs/plans/2026-10-11-evidence-strength-mapper.md` — new skill. Branch `build/evidence-strength-mapper`. Expected end state: `pytest skills/evidence-strength-mapper/tests/ -q` = 10 passed.

## Done =
- Both branches pushed, two PRs open against `main`, each PR body listing what was built and the passing test count.
- Full suite green: `pytest skills/ -q` → 26 passed.
- A one-paragraph sign-off summary per PR for Eleanor's morning review.
