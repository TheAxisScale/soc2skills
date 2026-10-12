---
name: evidence-strength-mapper
description: >
  Classify compliance evidence as system-of-record (strong) vs screenshot /
  self-authored / manual (weak), explain why, and suggest a stronger upgrade.
  Use whenever a user is gathering or reviewing evidence for a SOC 2 / ISO 27001 /
  HIPAA audit and wants to know which evidence will actually hold up — "substance,
  not screenshots." Takes a controls list (with evidence examples) or a raw list
  of evidence descriptions.
compatibility: Python 3.11+ stdlib; JSON + Markdown output
---

# Evidence Strength Mapper

For each control (or a raw list of evidence), classify every piece of evidence as
**strong** (pulled from the system of record) or **weak** (a screenshot,
self-authored document, or manual assertion), say *why*, and name the stronger
form to collect instead. This operationalizes **"substance, not screenshots."**

## Honesty contract (non-negotiable)

- **Never upgrade a "weak" verdict to sound reassuring.** A screenshot is weak even
  when the user is proud of it. Report it as weak and explain the risk.
- **Form beats content.** A *screenshot of a configuration export* is still weak —
  the weakness is in the form of the evidence, not its subject. The classifier
  checks "form" types (screenshot, manual claim) before content types, on purpose.
- **Unclassifiable evidence is flagged weak-until-proven**, never assumed strong.
- The "why" strings are grounded in the sourced research (`reference/evidence-taxonomy.json`),
  not invented.

## When to use

- A user is assembling evidence for an audit and asks which items will hold up.
- An auditor asked for screenshots and the user wants to know if that's good enough.
- Reviewing a control list (e.g. one produced by `audit-workplan-generator`) for
  evidence gaps.

This skill does **one** thing — classify evidence strength. It deliberately does
**not** bundle framework templates (that is `audit-workplan-generator`'s job); it
takes a controls list or raw evidence strings as input.

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
# or import directly
import sys; sys.path.insert(0, "scripts")
from evidence_mapper import strength_report, render_markdown
print(render_markdown(strength_report(controls)))
```

A **control** has the shape `{"id", "name", "evidence_examples": [str, ...]}`
(only `id`, `name`, and `evidence_examples` are used here).

## How to read the report

- **Weak %** leads the report — the headline number for how much of the evidence
  set is point-in-time, cherry-pickable, or self-authored.
- **All-weak controls** are the **highest risk**: controls with *no* strong
  evidence at all. Fix these first.
- Each weak item carries a **"Replace with"** upgrade — the stronger evidence form
  (export, log, ticket-with-approval, or independent report) to collect instead.

Strong evidence: configuration exports, automated logs / audit trails, API pulls,
tickets/PRs with approval, independent or tool-generated reports, signed/dated records.
Weak evidence: screenshots, manual assertions / email confirmations, self-authored
documents — and anything unclassifiable (weak until tied to a system of record).
