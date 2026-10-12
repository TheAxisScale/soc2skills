# evidence-strength-mapper — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A new Claude Skill that, for each control, classifies the suggested evidence as **system-of-record (strong)** vs **screenshot / self-authored / manual (weak)**, explains why, and suggests a stronger upgrade — operationalizing "substance, not screenshots."

**Architecture:** A fully-tested Python module (`scripts/evidence_mapper.py`) does the classification deterministically against a keyword taxonomy in `reference/evidence-taxonomy.json`. `SKILL.md` tells Claude to run it over the user's controls (or a raw evidence list) and present the strength report, never softening a "weak" verdict. Single responsibility: this skill classifies evidence strength only — it takes a controls list as input (e.g. produced by `audit-workplan-generator`) and does **not** bundle framework templates (DRY: that's the other skill's job).

**Tech Stack:** Python 3.11+, pytest, stdlib `json` only.

**Honesty rules:** a screenshot of a config export is still a screenshot (weak) — form beats content; unclassifiable evidence is flagged weak-until-proven, never assumed strong; the "why" strings are grounded in the sourced research, not invented.

**Working directory:** repo root = `honest-soc2-starter-kit/`. Paths are relative to it. Reuse the same venv as the other skill: `. .venv/bin/activate` (create with `python3 -m venv .venv && . .venv/bin/activate && pip install -q pytest` if starting fresh).

---

## File structure

- `skills/evidence-strength-mapper/scripts/evidence_mapper.py` — CREATE: the tested core.
- `skills/evidence-strength-mapper/tests/test_evidence_mapper.py` — CREATE: unit tests.
- `skills/evidence-strength-mapper/reference/evidence-taxonomy.json` — CREATE: evidence-type → strength keyword taxonomy.
- `skills/evidence-strength-mapper/SKILL.md` — CREATE: the skill definition.
- `skills/evidence-strength-mapper/evals.json` — CREATE: eval prompts.
- `skills/evidence-strength-mapper/README.md` — CREATE.

### Shared data model (keep names exact)

A **control** (same shape as the other skill): `{"id","name","objective","priority","effort_hours","evidence_examples":[str,...]}`. Only `id`, `name`, and `evidence_examples` are required here.

`classify_evidence(description)` returns: `{"description": str, "type": str, "strength": "strong"|"weak", "why": str, "upgrade_to": str|None}`.

---

### Task 1: Taxonomy + classify_evidence (with form-beats-content precedence)

**Files:**
- Create: `skills/evidence-strength-mapper/reference/evidence-taxonomy.json`
- Create: `skills/evidence-strength-mapper/scripts/evidence_mapper.py`
- Test: `skills/evidence-strength-mapper/tests/test_evidence_mapper.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/evidence-strength-mapper/tests/test_evidence_mapper.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import evidence_mapper as em


def test_screenshot_is_weak_and_suggests_export_upgrade():
    r = em.classify_evidence("Screenshot of MFA settings")
    assert r["type"] == "screenshot"
    assert r["strength"] == "weak"
    assert "export" in r["upgrade_to"].lower()


def test_config_export_is_strong():
    r = em.classify_evidence("MFA configuration export")
    assert r["type"] == "system_export"
    assert r["strength"] == "strong"
    assert r["upgrade_to"] is None


def test_form_beats_content_screenshot_of_export_is_still_weak():
    r = em.classify_evidence("Screenshot of the configuration export")
    assert r["type"] == "screenshot"       # screenshot checked before system_export
    assert r["strength"] == "weak"


def test_policy_document_is_weak_self_authored():
    r = em.classify_evidence("Information security policy document")
    assert r["type"] == "self_authored_doc"
    assert r["strength"] == "weak"


def test_pentest_report_is_strong():
    assert em.classify_evidence("Pentest report")["strength"] == "strong"


def test_unknown_defaults_to_weak_until_proven():
    r = em.classify_evidence("code of conduct")
    assert r["strength"] == "weak"
    assert r["type"] == "unclassified"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest skills/evidence-strength-mapper/tests/test_evidence_mapper.py -q`
Expected: FAIL — `ModuleNotFoundError`/`AttributeError` (no `evidence_mapper`).

- [ ] **Step 3: Create the taxonomy data**

Create `reference/evidence-taxonomy.json` (order matters — `classify_evidence` checks types top-to-bottom and returns the first keyword hit, so "form" types like screenshot/manual precede content types):

```json
{
  "source": "Axis GRC & Compliance Pain Research, 2026-10-11. Screenshot-weakness thesis: John Flack (GRC Engineering Club); Ann Wallace (Edera). Performative-GRC/self-authored thesis: Nirosh Jayaratnam.",
  "types": [
    {"type": "screenshot", "label": "Screenshot of a settings screen", "strength": "weak", "keywords": ["screenshot", "screen shot", "screengrab", "snip"], "why": "One setting, on one screen, at one moment, chosen by the auditee. Stale within hours, cherry-pickable, point-in-time not period, and it can't show prevention.", "upgrade_of": "system_export"},
    {"type": "manual_claim", "label": "Manual assertion / email confirmation", "strength": "weak", "keywords": ["confirm", "verbal", "manually", "we attest", "email saying"], "why": "An assertion, not evidence. An auditor cannot reperform it.", "upgrade_of": "ticket_with_approval"},
    {"type": "system_export", "label": "Configuration export from the system of record", "strength": "strong", "keywords": ["export", "configuration", "config", "settings"], "why": "Pulled from the system of record; reflects the actually-enforced state, not a staged view.", "upgrade_of": null},
    {"type": "automated_log", "label": "Automated log / audit trail", "strength": "strong", "keywords": ["log", "audit trail", "siem", "alert", "monitoring"], "why": "A time-series record over the whole period; hard to cherry-pick a single moment.", "upgrade_of": null},
    {"type": "api_pull", "label": "Programmatic API pull", "strength": "strong", "keywords": ["api"], "why": "Reproducible and covers all resources, not a sampled screen.", "upgrade_of": null},
    {"type": "ticket_with_approval", "label": "Ticket / PR with approval", "strength": "strong", "keywords": ["ticket", "approval", "pull request", "pr review", "change request", "sign-off"], "why": "Shows the control operated with authorization and a reviewer, across many instances.", "upgrade_of": null},
    {"type": "third_party_report", "label": "Independent or tool-generated report", "strength": "strong", "keywords": ["report", "scan", "pentest", "penetration", "dr test", "test results"], "why": "Independent or tool-generated; not authored by the auditee.", "upgrade_of": null},
    {"type": "signed_record", "label": "Signed / dated record", "strength": "strong", "keywords": ["signed", "baa", "acknowledgement", "records", "record"], "why": "A dated, attributable record of a real event.", "upgrade_of": null},
    {"type": "self_authored_doc", "label": "Self-authored document", "strength": "weak", "keywords": ["policy", "policies", "document", "plan", "procedure", "attestation", "spreadsheet", "classification", "schedule", "matrix", "chart", "minutes", "inventory", "register"], "why": "Proves a document exists, not that the control operated. Templates you didn't write and can't defend are the classic 'performative GRC' trap.", "upgrade_of": "automated_log"}
  ],
  "unclassified": {"type": "unclassified", "strength": "weak", "why": "Could not match a known evidence type. Treat as weak until you can tie it to a system of record.", "upgrade_to": "tie it to a system of record (export, log, ticket, or report)"}
}
```

Create the module:

```python
# skills/evidence-strength-mapper/scripts/evidence_mapper.py
"""Deterministic evidence-strength classifier for the evidence-strength-mapper skill.

Pure stdlib. Form beats content: a screenshot of a config export is still weak,
because the weakness is in the *form* of the evidence, not its subject."""
import json
import pathlib

_TAX = json.loads((pathlib.Path(__file__).resolve().parents[1] / "reference" / "evidence-taxonomy.json").read_text())
_LABELS = {t["type"]: t["label"] for t in _TAX["types"]}


def classify_evidence(description):
    """Classify a free-text evidence description into a type + strength, with an
    honest 'why' and (for weak evidence) the stronger form to collect instead."""
    text = description.lower()
    for t in _TAX["types"]:  # order defines precedence
        if any(k in text for k in t["keywords"]):
            upgrade = _LABELS.get(t["upgrade_of"]) if t.get("upgrade_of") else None
            return {"description": description, "type": t["type"], "strength": t["strength"], "why": t["why"], "upgrade_to": upgrade}
    u = _TAX["unclassified"]
    return {"description": description, "type": u["type"], "strength": u["strength"], "why": u["why"], "upgrade_to": u["upgrade_to"]}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest skills/evidence-strength-mapper/tests/test_evidence_mapper.py -q`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add skills/evidence-strength-mapper/scripts/evidence_mapper.py skills/evidence-strength-mapper/reference/evidence-taxonomy.json skills/evidence-strength-mapper/tests/test_evidence_mapper.py
git commit -m "feat(evidence): taxonomy + strength classifier (form beats content)"
```

---

### Task 2: map_control

**Files:**
- Modify: `skills/evidence-strength-mapper/scripts/evidence_mapper.py`
- Test: `skills/evidence-strength-mapper/tests/test_evidence_mapper.py`

- [ ] **Step 1: Write the failing test**

```python
# append to test_evidence_mapper.py
def test_map_control_classifies_each_example_and_flags_all_weak():
    control = {"id": "CC1.1", "name": "Control environment", "evidence_examples": ["code of conduct", "org chart", "board minutes"]}
    r = em.map_control(control)
    assert r["control_id"] == "CC1.1"
    assert len(r["evidence"]) == 3
    assert r["all_weak"] is True  # none of these prove operation


def test_map_control_not_all_weak_when_a_strong_item_present():
    control = {"id": "CC6.1", "name": "Access", "evidence_examples": ["Screenshot of MFA settings", "MFA configuration export"]}
    r = em.map_control(control)
    assert r["all_weak"] is False
    strengths = {e["strength"] for e in r["evidence"]}
    assert strengths == {"weak", "strong"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest skills/evidence-strength-mapper/tests/test_evidence_mapper.py -q`
Expected: FAIL — missing `map_control`.

- [ ] **Step 3: Write implementation**

```python
# append to evidence_mapper.py
def map_control(control):
    """Classify every evidence example for one control. `all_weak` flags controls
    whose entire evidence set is weak — the highest-risk gaps for an audit."""
    classified = [classify_evidence(ex) for ex in control.get("evidence_examples", [])]
    all_weak = bool(classified) and all(e["strength"] == "weak" for e in classified)
    return {
        "control_id": control["id"],
        "name": control.get("name", ""),
        "evidence": classified,
        "all_weak": all_weak,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest skills/evidence-strength-mapper/tests/test_evidence_mapper.py -q`
Expected: PASS (8 passed).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(evidence): per-control mapping with all-weak flag"
```

---

### Task 3: strength_report aggregation

**Files:**
- Modify: `skills/evidence-strength-mapper/scripts/evidence_mapper.py`
- Test: `skills/evidence-strength-mapper/tests/test_evidence_mapper.py`

- [ ] **Step 1: Write the failing test**

```python
# append to test_evidence_mapper.py
def test_strength_report_summarizes_counts_and_weakest_controls():
    controls = [
        {"id": "C1", "name": "a", "evidence_examples": ["Screenshot of settings", "policy document"]},  # all weak
        {"id": "C2", "name": "b", "evidence_examples": ["SIEM log", "change ticket with approval"]},     # all strong
    ]
    rep = em.strength_report(controls)
    assert rep["summary"]["total"] == 4
    assert rep["summary"]["strong"] == 2
    assert rep["summary"]["weak"] == 2
    assert rep["summary"]["weak_pct"] == 50.0
    assert rep["summary"]["all_weak_controls"] == ["C1"]
    assert len(rep["controls"]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest skills/evidence-strength-mapper/tests/test_evidence_mapper.py -q`
Expected: FAIL — missing `strength_report`.

- [ ] **Step 3: Write implementation**

```python
# append to evidence_mapper.py
def strength_report(controls):
    """Aggregate per-control mappings into a portfolio view: strong vs weak
    counts, weak %, and the controls that have no strong evidence at all."""
    mapped = [map_control(c) for c in controls]
    items = [e for m in mapped for e in m["evidence"]]
    strong = sum(1 for e in items if e["strength"] == "strong")
    weak = sum(1 for e in items if e["strength"] == "weak")
    total = len(items)
    return {
        "controls": mapped,
        "summary": {
            "total": total,
            "strong": strong,
            "weak": weak,
            "weak_pct": round(100 * weak / total, 1) if total else 0.0,
            "all_weak_controls": [m["control_id"] for m in mapped if m["all_weak"]],
        },
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest skills/evidence-strength-mapper/tests/test_evidence_mapper.py -q`
Expected: PASS (9 passed).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(evidence): portfolio strength report"
```

---

### Task 4: Markdown rendering + CLI

**Files:**
- Modify: `skills/evidence-strength-mapper/scripts/evidence_mapper.py`
- Test: `skills/evidence-strength-mapper/tests/test_evidence_mapper.py`

- [ ] **Step 1: Write the failing test**

```python
# append to test_evidence_mapper.py
def test_render_markdown_leads_with_weak_pct_and_upgrades():
    controls = [{"id": "C1", "name": "Access", "evidence_examples": ["Screenshot of MFA settings"]}]
    md = em.render_markdown(em.strength_report(controls))
    assert "Substance, not screenshots" in md
    assert "%" in md
    assert "Replace with" in md  # upgrade guidance for the weak item
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest skills/evidence-strength-mapper/tests/test_evidence_mapper.py -q`
Expected: FAIL — missing `render_markdown`.

- [ ] **Step 3: Write implementation**

```python
# append to evidence_mapper.py
def render_markdown(report):
    s = report["summary"]
    lines = [
        "# Evidence Strength Report",
        "",
        "> Substance, not screenshots.",
        "",
        f"**{s['weak_pct']}% of your evidence is weak** ({s['weak']} weak / {s['strong']} strong of {s['total']}).",
    ]
    if s["all_weak_controls"]:
        lines.append(f"**Highest risk — controls with *no* strong evidence:** {', '.join(s['all_weak_controls'])}")
    lines.append("")
    for m in report["controls"]:
        lines.append(f"## {m['control_id']} — {m['name']}")
        for e in m["evidence"]:
            mark = "✅" if e["strength"] == "strong" else "⚠️"
            lines.append(f"- {mark} **{e['strength']}** · {e['description']} — {e['why']}")
            if e["upgrade_to"]:
                lines.append(f"  - ↳ Replace with: {e['upgrade_to']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    import argparse, sys
    ap = argparse.ArgumentParser(description="Map evidence strength: system-of-record vs screenshot.")
    ap.add_argument("--controls", help="path to a JSON file: a list of controls, or {\"controls\":[...]}")
    ap.add_argument("--evidence", help="semicolon-separated evidence descriptions (ad-hoc, no controls)")
    ap.add_argument("--format", choices=["json", "md"], default="md")
    a = ap.parse_args()
    if a.controls:
        data = json.loads(pathlib.Path(a.controls).read_text())
        controls = data["controls"] if isinstance(data, dict) else data
    elif a.evidence:
        controls = [{"id": "ad-hoc", "name": "", "evidence_examples": [e.strip() for e in a.evidence.split(";") if e.strip()]}]
    else:
        print("Provide --controls <file.json> or --evidence \"a; b; c\"", file=sys.stderr)
        raise SystemExit(2)
    rep = strength_report(controls)
    print(json.dumps(rep, indent=2) if a.format == "json" else render_markdown(rep))
```

- [ ] **Step 4: Run test to verify it passes + smoke-test CLI**

Run: `. .venv/bin/activate && pytest skills/evidence-strength-mapper/tests/test_evidence_mapper.py -q`
Expected: PASS (10 passed).
Run: `python skills/evidence-strength-mapper/scripts/evidence_mapper.py --evidence "Screenshot of MFA settings; SIEM audit log; access control policy"`
Expected: Markdown showing weak %, ⚠️/✅ marks, and "Replace with" upgrades.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(evidence): markdown report + CLI entry point"
```

---

### Task 5: SKILL.md + evals

**Files:**
- Create: `skills/evidence-strength-mapper/SKILL.md`
- Create: `skills/evidence-strength-mapper/evals.json`

- [ ] **Step 1: Write SKILL.md**

YAML frontmatter then body. Required frontmatter:

```yaml
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
```

Body must cover: the honesty contract (never upgrade a "weak" verdict to sound reassuring; form beats content); when to use; how to run (`python scripts/evidence_mapper.py --controls file.json` or `--evidence "a; b; c"`, or import `strength_report`); how to read the report (weak %, all-weak controls = highest risk); and that unclassified evidence is flagged weak-until-proven on purpose.

- [ ] **Step 2: Write evals.json** (mirror the audit-workplan evals format)

```json
{
  "skill_name": "evidence-strength-mapper",
  "evals": [
    {"id": 1, "eval_name": "control-list-with-mixed-evidence", "prompt": "Here are 10 SOC 2 controls with the evidence I'm planning to collect. Tell me which evidence is strong vs weak and what I should collect instead.", "expected_output": "Strength report: weak %, controls with no strong evidence flagged as highest risk, and a concrete upgrade for each weak item.", "files": ["controls.json"]},
    {"id": 2, "eval_name": "screenshot-heavy-review", "prompt": "My auditor wants screenshots of all my settings. Are screenshots good enough? Here's my list.", "expected_output": "Honest explanation that screenshots are the weakest evidence (point-in-time, cherry-pickable, can't show prevention) with system-of-record upgrades; does not soften the verdict.", "files": []},
    {"id": 3, "eval_name": "ad-hoc-evidence-strings", "prompt": "Is 'we confirm via email that access was removed' acceptable evidence for access deprovisioning?", "expected_output": "Classifies as a manual claim (weak) and suggests a ticket/PR-with-approval or deprovisioning log instead.", "files": []}
  ]
}
```

- [ ] **Step 3: Verify frontmatter + commit**

Run: `head -12 skills/evidence-strength-mapper/SKILL.md`
Expected: valid YAML frontmatter with `name:` and `description:`.

```bash
git add skills/evidence-strength-mapper/SKILL.md skills/evidence-strength-mapper/evals.json
git commit -m "docs(evidence): SKILL.md + evals"
```

---

### Task 6: README + full suite green

**Files:**
- Create: `skills/evidence-strength-mapper/README.md`

- [ ] **Step 1: Write the README**

Cover: one-line purpose, the "form beats content" principle, how to run (CLI + import), example output (paste the Task 4 smoke-test sample), and "what it will not do" (call weak evidence strong to make you feel better).

- [ ] **Step 2: Run the whole repo test suite**

Run: `. .venv/bin/activate && pytest skills/ -q`
Expected: PASS — both skills green (16 + 10 = 26 passed), zero failures.

- [ ] **Step 3: Commit**

```bash
git add skills/evidence-strength-mapper/README.md
git commit -m "docs(evidence): skill README with example output"
```

---

## Self-review (completed during planning)

- **Spec coverage:** classifier (T1), per-control mapping (T2), portfolio report (T3), rendering+CLI (T4), SKILL.md+evals (T5), README+green (T6). The spec's core promise — strong vs weak tagging with upgrades — is T1–T3. ✅
- **Placeholder scan:** taxonomy data is real; every code step is complete; no TODOs. ✅
- **Type consistency:** `classify_evidence` return keys (`description/type/strength/why/upgrade_to`) are consumed unchanged by `map_control` and `render_markdown`; `strength_report.summary` keys match the test. The `upgrade_to` field resolves a *type* to its human **label** via `_LABELS`, consistently. ✅
- **DRY/standalone:** deliberately does not bundle frameworks (that's audit-workplan-generator); input is a controls list or raw strings. ✅
