# audit-workplan-generator

Generate an **honest** audit-prep workplan for SOC 2, ISO 27001, or HIPAA: prioritized controls, a feasibility traffic-light, phased timeline, scope-reduction options, a Monday-morning top-3, and sourced all-in cost ranges.

## Honesty contract

This skill **never claims a timeline is achievable when the capacity math says otherwise, and never invents costs or evidence.** All decision logic lives in the deterministic, unit-tested core (`scripts/workplan.py`), so recommendations are reproducible — no optimistic rounding, no invented numbers.

- 🔴 is reported as 🔴. A tight plan is 🟡. Only genuinely comfortable capacity is 🟢.
- Cost ranges are the sourced ranges from `reference/cost-ranges.json`, cited with their source.
- A green light means *the numbers work*, not that the audit will pass.

## How to run

```bash
# CLI — Markdown (default) or JSON for app integration
python scripts/workplan.py --framework soc2 --weeks 16 --team-size 3 --concerns "encryption,change management"
python scripts/workplan.py --framework iso27001 --weeks 12 --team-size 2 --format json
```

```python
# Import directly
import sys; sys.path.insert(0, "scripts")
from workplan import build_workplan, render_markdown
plan = build_workplan(framework="soc2", weeks=16, team_size=3, concerns=["encryption"])
print(render_markdown(plan))
```

`build_workplan` takes either a bundled `framework` name **or** an explicit `controls` list
(same shape as the bundled templates: `id`, `name`, `objective`, `priority`, `effort_hours`, `evidence_examples`).

## Bundled frameworks

Seed a plan without any spreadsheet via `load_framework(name)`:

| name | framework | controls |
|------|-----------|----------|
| `soc2` | SOC 2 (2017 TSC, rev. 2022) | 13 |
| `iso27001` | ISO 27001 (2022 Annex A) | 12 |
| `hipaa` | HIPAA Security Rule | 10 |

These are representative seeds with a documented schema — expand them following the same shape.

## Example output

```
# SOC 2 Audit Prep Workplan

**Feasibility:** 🔴 Unrealistic at this capacity. Reduce scope, add people, or extend the timeline (see scope options).
(needs ~170h, you have ~30h at this capacity)

## Start Monday (top 3)
- **CC5.2** — Change management
- **CC6.1** — Logical access controls
- **CC6.2** — Access provisioning & deprovisioning

## If the timeline is tight, consider:
- **Critical only** (4 controls, ~66h): 🔴 Unrealistic at this capacity. ...
- **Critical + high** (10 controls, ~144h): 🔴 Unrealistic at this capacity. ...

## Honest all-in cost
- Implementation / advisory: $10,000–$25,000
- Independent audit: $10,000–$50,000
- Most first-timers underestimate the all-in by 30–50%.
```

## What it deliberately will not do

- **Fabricate costs.** Figures come only from the sourced reference data.
- **Promise an unrealistic timeline.** If the capacity math is 🔴, it says 🔴 and offers honest reduced-scope options instead.
- **Claim the audit will pass.** It estimates effort and cost; passing depends on the work you do.

## Tests

```bash
pytest skills/audit-workplan-generator/tests/ -q
```
