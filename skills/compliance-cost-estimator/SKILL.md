---
name: compliance-cost-estimator
description: >-
  Returns the all-in cost of a SOC 2 / ISO 27001 / HIPAA program — tooling +
  implementation/advisory + independent audit — and surfaces the hidden-cost
  gap, the per-framework tax, and the Year-2 renewal jump. Every figure is
  sourced; it never invents a tool price. Use when someone asks what SOC 2 (or
  ISO 27001 / HIPAA) really costs, why the subscription isn't the whole bill,
  why adding frameworks gets expensive, or why their Year-2 renewal jumped.
---

# compliance-cost-estimator

Estimates the **all-in** cost of a compliance program and names the costs
founders routinely miss. The subscription is the small number; the all-in
(tooling + implementation/advisory + independent audit) is what actually lands.

## Honesty contract (non-negotiable)

- **Every number traces to a source.** All ranges come from
  `reference/cost-model.json`, whose `source` field names the research behind
  them. Nothing is invented.
- **Never invent a tooling price.** Platform pricing is quote-specific and
  varies widely. If the user supplies a figure, include it; otherwise the
  output shows tooling as "varies — supply your quote." Do not guess a number.
- **Always state it's an estimate, not a quote**, and surface the assumptions
  (the ranges, the per-framework tax, the renewal jump). The output's
  `disclaimer` field says this; keep it.

## When to use

- "What does SOC 2 actually cost?" / "Is the Vanta/Drata subscription the whole bill?"
- "We want SOC 2 and ISO 27001 — what's the combined cost?"
- "Why did my Year-2 renewal go up so much?"
- Budgeting a first audit, or a multi-framework program.

## How to run

**CLI:**

```bash
python skills/compliance-cost-estimator/scripts/cost_estimator.py \
  --frameworks soc2,iso27001
# optional tooling quote the user gives you:
python skills/compliance-cost-estimator/scripts/cost_estimator.py \
  --frameworks soc2 --tooling-low 6000 --tooling-high 6000
# machine-readable:
python skills/compliance-cost-estimator/scripts/cost_estimator.py \
  --frameworks soc2 --format json
```

**As an import:**

```python
import cost_estimator as ce
e = ce.estimate(["soc2", "iso27001"], tooling_annual=[6000, 6000])  # tooling optional
print(ce.render_markdown(e))
```

`estimate(frameworks, tooling_annual=None)` takes a list of framework keys
(`soc2`, `iso27001`, `hipaa`, …) and an optional `[low, high]` tooling figure.

## How to read the output

- **All-in total** — the full range: implementation/advisory + independent
  audit (per framework) + per-framework tax + tooling (if supplied).
- **Line items** — each cost broken out. Tooling shows "varies" unless the user
  gave a quote.
- **Watch out** — the three facts founders miss:
  1. Subscription-only budgeters **underestimate the all-in by 30-50%**.
  2. The **renewal trap**: Year-1 discounts revert to list; budget a **20-40%**
     Year-2 increase and watch the **30-day** auto-renewal notice window.
  3. The **per-framework tax**: each framework beyond the first ≈ **$5K/yr**,
     escalating past 3 frameworks.

Always present the result as an estimate and point the user to the `source`.
