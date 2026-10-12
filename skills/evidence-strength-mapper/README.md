# evidence-strength-mapper

Classify compliance evidence as **system-of-record (strong)** vs **screenshot / self-authored / manual (weak)**, explain *why*, and suggest a stronger upgrade for every weak item. Operationalizes **"substance, not screenshots."**

## The "form beats content" principle

The weakness of evidence is in its **form**, not its subject. A *screenshot of a configuration export* is still weak — it's a point-in-time, cherry-pickable image, no matter what it depicts. So the classifier checks "form" types (screenshot, manual claim) **before** content types, on purpose. Unclassifiable evidence is flagged **weak-until-proven**, never assumed strong.

## How to run

```bash
# From a controls JSON file (a list of controls, or {"controls":[...]})
python scripts/evidence_mapper.py --controls controls.json

# Ad-hoc, from semicolon-separated evidence descriptions
python scripts/evidence_mapper.py --evidence "Screenshot of MFA settings; SIEM audit log; access control policy"

# --format json for app integration (Markdown is the default)
python scripts/evidence_mapper.py --controls controls.json --format json
```

```python
# Import directly
import sys; sys.path.insert(0, "scripts")
from evidence_mapper import strength_report, render_markdown, classify_evidence
print(render_markdown(strength_report(controls)))
```

A **control** has the shape `{"id", "name", "evidence_examples": [str, ...]}`.
This skill does **not** bundle framework templates — that's `audit-workplan-generator`'s
job. It takes a controls list (e.g. produced by that skill) or raw evidence strings.

## Example output

```
# Evidence Strength Report

> Substance, not screenshots.

**66.7% of your evidence is weak** (2 weak / 1 strong of 3).

## ad-hoc —
- ⚠️ **weak** · Screenshot of MFA settings — One setting, on one screen, at one moment,
  chosen by the auditee. Stale within hours, cherry-pickable, point-in-time not period,
  and it can't show prevention.
  - ↳ Replace with: Configuration export from the system of record
- ✅ **strong** · SIEM audit log — A time-series record over the whole period; hard to
  cherry-pick a single moment.
- ⚠️ **weak** · access control policy — Proves a document exists, not that the control
  operated. ...
  - ↳ Replace with: Automated log / audit trail
```

## What it will not do

- **Call weak evidence strong to make you feel better.** A screenshot is weak even when
  you're proud of it; the verdict is never softened.
- Assume unknown evidence is strong — unclassifiable items are weak until tied to a
  system of record.
- Invent the "why" — reasons are grounded in the sourced taxonomy (`reference/evidence-taxonomy.json`).

## Tests

```bash
pytest skills/evidence-strength-mapper/tests/ -q
```
