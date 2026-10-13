# compliance-cost-estimator

A deterministic, stdlib-only estimator for the **all-in** cost of a SOC 2 /
ISO 27001 / HIPAA program: tooling + implementation/advisory + independent
audit. It surfaces the three costs founders routinely miss — the hidden-cost
gap, the per-framework tax, and the Year-2 renewal jump.

## Purpose

The subscription is the small number. The all-in is what actually lands, and
subscription-only budgeters **underestimate it by 30-50%**. This skill turns a
list of frameworks (plus an optional tooling quote) into a sourced range and
the warnings that go with it.

## Honesty contract

- Every figure traces to `reference/cost-model.json` → its `source`.
  Nothing is invented.
- **Tooling price is never invented.** It's treated as user-supplied, or shown
  as "varies — supply your quote."
- Output always states it's an **estimate, not a quote**, and shows its
  assumptions.

## Usage

**CLI:**

```bash
python skills/compliance-cost-estimator/scripts/cost_estimator.py --frameworks soc2,iso27001
```

Optional flags: `--tooling-low` / `--tooling-high` (your platform quote),
`--format json|md` (default `md`).

**Import:**

```python
import cost_estimator as ce
e = ce.estimate(["soc2", "iso27001"], tooling_annual=[6000, 6000])  # tooling optional
print(ce.render_markdown(e))
```

## Example output

```
# All-in compliance cost — soc2, iso27001

**All-in total: $35,000-$130,000**

## Line items
- Implementation / advisory: $10,000-$25,000
- Independent audit: $20,000-$100,000
- Per-framework tax: $5,000
- Tooling: varies — supply your quote

## Watch out
- Most first-timers underestimate the all-in by 30-50%.
- Year-1 startup discounts (up to ~70% off) can revert to list once you're locked in via evidence history/integrations. Watch the 30-day auto-renewal notice window; budget a 20-40% Year-2 increase.
- Each framework beyond the first can add ~$5K/yr on major platforms; costs escalate past 3 frameworks.

_Axis GRC & Compliance Pain Research, 2026-10-11 (adversarially verified)_

> This is an estimate, not a quote. Ranges are sourced (see 'source'); tooling price is yours to supply, never invented. Most first-timers underestimate the all-in by 30-50%.
```

## What it won't do

- **Invent a tooling/platform price.** Platform pricing is quote-specific; the
  skill shows "varies" unless you supply a figure.
- **Give a guaranteed quote.** Output is a sourced estimate, not a binding
  number. Real costs depend on scope, vendor, and company size.

## Tests

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -q pytest
pytest skills/compliance-cost-estimator/tests/ -q   # 6 passed
```
