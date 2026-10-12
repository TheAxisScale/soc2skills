# audit-workplan-generator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the `audit-workplan-generator` Claude Skill by adding the five gaps identified in testing (feasibility traffic-light, scope-reduction, Monday-morning top-3, framework templates, external-cost ranges), backed by a tested Python core.

**Architecture:** The skill is a `SKILL.md` that orchestrates a small, fully-tested Python module (`scripts/workplan.py`). All decision logic (prioritization, feasibility, phasing, scope reduction) lives in Python so it is deterministic and unit-tested; `SKILL.md` tells Claude when and how to call it and how to present the result honestly. Framework control templates live as JSON reference data so the skill works even when the user has no spreadsheet.

**Tech Stack:** Python 3.11+, pytest. No third-party deps for the core (stdlib `json` only). Excel export is deferred (openpyxl) and out of scope for this plan — JSON + Markdown output only.

**Honesty rules (non-negotiable, from the spec):** never claim a timeline is achievable when the numbers say otherwise; every cost range is the sourced range from the research, not invented; output must say "estimate" and show the assumptions.

**Working directory:** repo root = `honest-soc2-starter-kit/`. All paths below are relative to it. Run `cd` into the repo root once before starting.

**Setup (run once, not a task):**
```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -q pytest
```

---

## File structure

- `skills/audit-workplan-generator/SKILL.md` — MODIFY (exists): add the five gaps.
- `skills/audit-workplan-generator/scripts/workplan.py` — CREATE: the tested core.
- `skills/audit-workplan-generator/tests/test_workplan.py` — CREATE: unit tests.
- `skills/audit-workplan-generator/reference/frameworks/soc2.json` — CREATE: SOC 2 control template.
- `skills/audit-workplan-generator/reference/frameworks/iso27001.json` — CREATE: ISO 27001 template.
- `skills/audit-workplan-generator/reference/frameworks/hipaa.json` — CREATE: HIPAA template.
- `skills/audit-workplan-generator/reference/cost-ranges.json` — CREATE: sourced external-cost ranges.
- `skills/audit-workplan-generator/README.md` — CREATE: how to use.
- `skills/audit-workplan-generator/evals.json` — exists (migrated); verified unchanged.

### Shared data model (used by every task — keep names exact)

A **control** (reference JSON entry and in-memory dict):
```json
{"id": "CC6.1", "name": "Logical access controls", "objective": "Restrict logical access to authorized users", "priority": "critical", "effort_hours": 20, "evidence_examples": ["MFA configuration export", "quarterly access review records"]}
```
`priority` ∈ `{"critical","high","medium","low"}`. `effort_hours` is an int.

A **framework file**: `{"framework": "SOC 2", "version": "...", "controls": [control, ...]}`.

**feasibility()** returns: `{"required_hours": int, "available_hours": int, "ratio": float, "light": "green"|"yellow"|"red", "verdict": str}`.

---

### Task 1: Priority ranking helper

**Files:**
- Create: `skills/audit-workplan-generator/scripts/workplan.py`
- Test: `skills/audit-workplan-generator/tests/test_workplan.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/audit-workplan-generator/tests/test_workplan.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import workplan


def test_prioritize_orders_critical_first():
    controls = [
        {"id": "A", "name": "a", "objective": "", "priority": "low", "effort_hours": 5, "evidence_examples": []},
        {"id": "B", "name": "b", "objective": "", "priority": "critical", "effort_hours": 5, "evidence_examples": []},
        {"id": "C", "name": "c", "objective": "", "priority": "high", "effort_hours": 5, "evidence_examples": []},
    ]
    ordered = workplan.prioritize(controls)
    assert [c["id"] for c in ordered] == ["B", "C", "A"]


def test_prioritize_bumps_controls_matching_concerns():
    controls = [
        {"id": "ENC", "name": "Data encryption", "objective": "encrypt data", "priority": "medium", "effort_hours": 5, "evidence_examples": []},
        {"id": "DOC", "name": "Documentation", "objective": "write docs", "priority": "high", "effort_hours": 5, "evidence_examples": []},
    ]
    ordered = workplan.prioritize(controls, concerns=["encryption"])
    assert ordered[0]["id"] == "ENC"  # concern match outranks nominal priority
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: FAIL — `AttributeError: module 'workplan' has no attribute 'prioritize'`.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/audit-workplan-generator/scripts/workplan.py
"""Deterministic core for the audit-workplan-generator skill.

Pure stdlib. All logic here is unit-tested so the skill's recommendations are
reproducible and honest (no invented numbers, no optimistic rounding)."""
import json
import pathlib

_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def prioritize(controls, concerns=None):
    """Return controls ordered critical-first. A control whose name/objective
    matches any concern keyword is promoted ahead of its nominal priority."""
    concerns = [c.lower() for c in (concerns or [])]

    def matches_concern(ctrl):
        text = (ctrl["name"] + " " + ctrl.get("objective", "")).lower()
        return any(k in text for k in concerns)

    return sorted(
        controls,
        key=lambda c: (0 if matches_concern(c) else 1, _RANK.get(c["priority"], 9)),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add skills/audit-workplan-generator/scripts/workplan.py skills/audit-workplan-generator/tests/test_workplan.py
git commit -m "feat(workplan): priority ranking with concern-based promotion"
```

---

### Task 2: Feasibility traffic-light (gap #1)

**Files:**
- Modify: `skills/audit-workplan-generator/scripts/workplan.py`
- Test: `skills/audit-workplan-generator/tests/test_workplan.py`

- [ ] **Step 1: Write the failing test**

```python
# append to test_workplan.py
def test_feasibility_green_when_capacity_exceeds_need():
    f = workplan.feasibility(required_hours=100, weeks=10, team_size=3, hours_per_person_per_week=5)
    # available = 10*3*5 = 150 >= 100  -> comfortable
    assert f["available_hours"] == 150
    assert f["light"] == "green"


def test_feasibility_yellow_when_tight():
    f = workplan.feasibility(required_hours=140, weeks=10, team_size=3, hours_per_person_per_week=5)
    # ratio = 140/150 = 0.93 -> tight
    assert f["light"] == "yellow"


def test_feasibility_red_when_underwater():
    f = workplan.feasibility(required_hours=300, weeks=10, team_size=3, hours_per_person_per_week=5)
    assert f["light"] == "red"
    assert "not" in f["verdict"].lower() or "unrealistic" in f["verdict"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: FAIL — `AttributeError: module 'workplan' has no attribute 'feasibility'`.

- [ ] **Step 3: Write minimal implementation**

```python
# append to workplan.py
def feasibility(required_hours, weeks, team_size, hours_per_person_per_week=5):
    """Honest capacity check. Thresholds: ratio<=0.8 green, <=1.0 yellow, >1.0 red.
    hours_per_person_per_week default 5 = realistic compliance side-work, not a
    full-time assumption (the test data showed enterprise plans over-estimate by
    assuming FTEs)."""
    available = weeks * team_size * hours_per_person_per_week
    ratio = required_hours / available if available else float("inf")
    if ratio <= 0.8:
        light, verdict = "green", "Achievable with the stated team and timeline."
    elif ratio <= 1.0:
        light, verdict = "yellow", "Tight. Achievable only if nothing slips — protect the critical path."
    else:
        light, verdict = "red", "Unrealistic at this capacity. Reduce scope, add people, or extend the timeline (see scope options)."
    return {
        "required_hours": required_hours,
        "available_hours": available,
        "ratio": round(ratio, 2),
        "light": light,
        "verdict": verdict,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(workplan): honest feasibility traffic-light (gap #1)"
```

---

### Task 3: Phase plan + Monday-morning top-3 (gap #3)

**Files:**
- Modify: `skills/audit-workplan-generator/scripts/workplan.py`
- Test: `skills/audit-workplan-generator/tests/test_workplan.py`

- [ ] **Step 1: Write the failing test**

```python
# append to test_workplan.py
def _sample_controls():
    return [
        {"id": "G1", "name": "Governance policy", "objective": "", "priority": "critical", "effort_hours": 10, "evidence_examples": ["policy doc"]},
        {"id": "AC1", "name": "Access control", "objective": "", "priority": "critical", "effort_hours": 20, "evidence_examples": ["MFA export"]},
        {"id": "EV1", "name": "Evidence refresh", "objective": "", "priority": "high", "effort_hours": 15, "evidence_examples": ["logs"]},
        {"id": "DR1", "name": "DR test", "objective": "", "priority": "medium", "effort_hours": 12, "evidence_examples": ["dr report"]},
    ]


def test_phase_plan_splits_into_four_phases_and_sums_effort():
    phases = workplan.phase_plan(_sample_controls(), weeks=16)
    assert len(phases) == 4
    total = sum(p["effort_hours"] for p in phases)
    assert total == 57  # 10+20+15+12
    # phase 1 carries the earliest (highest-priority) work
    assert "AC1" in phases[0]["control_ids"] or "G1" in phases[0]["control_ids"]


def test_monday_top3_returns_three_highest_priority():
    top = workplan.monday_top3(_sample_controls())
    assert len(top) == 3
    assert {t["id"] for t in top} == {"G1", "AC1", "EV1"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: FAIL — missing `phase_plan` / `monday_top3`.

- [ ] **Step 3: Write minimal implementation**

```python
# append to workplan.py
_PHASE_NAMES = [
    "Foundation & critical path",
    "Operational controls & evidence",
    "Evidence gap closure",
    "Final preparation",
]


def phase_plan(controls, weeks, phases=4):
    """Split prioritized controls across `phases` buckets, critical work first.
    Week ranges are divided evenly across the available timeline."""
    ordered = prioritize(controls)
    buckets = [[] for _ in range(phases)]
    for i, ctrl in enumerate(ordered):
        buckets[i % phases].append(ctrl)  # round-robin keeps each phase balanced after priority sort
    span = max(1, weeks // phases)
    out = []
    for i, bucket in enumerate(buckets):
        start = i * span + 1
        end = weeks if i == phases - 1 else (i + 1) * span
        out.append({
            "phase": i + 1,
            "name": _PHASE_NAMES[i] if i < len(_PHASE_NAMES) else f"Phase {i+1}",
            "weeks": f"{start}-{end}",
            "control_ids": [c["id"] for c in bucket],
            "effort_hours": sum(c["effort_hours"] for c in bucket),
        })
    return out


def monday_top3(controls):
    """The three things to start this week: the highest-priority controls."""
    return prioritize(controls)[:3]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(workplan): phase plan + Monday-morning top-3 (gap #3)"
```

---

### Task 4: Scope-reduction options (gap #2)

**Files:**
- Modify: `skills/audit-workplan-generator/scripts/workplan.py`
- Test: `skills/audit-workplan-generator/tests/test_workplan.py`

- [ ] **Step 1: Write the failing test**

```python
# append to test_workplan.py
def test_scope_options_only_offered_when_not_green():
    controls = _sample_controls()
    # plenty of capacity -> no reduction needed
    assert workplan.scope_options(controls, weeks=16, team_size=4) == []


def test_scope_options_offer_critical_only_when_red():
    controls = _sample_controls()
    opts = workplan.scope_options(controls, weeks=2, team_size=1)
    assert len(opts) >= 1
    critical_only = next(o for o in opts if o["name"] == "Critical only")
    assert set(critical_only["control_ids"]) == {"G1", "AC1"}
    assert critical_only["feasibility"]["light"] in ("green", "yellow")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: FAIL — missing `scope_options`.

- [ ] **Step 3: Write minimal implementation**

```python
# append to workplan.py
def _total_hours(controls):
    return sum(c["effort_hours"] for c in controls)


def scope_options(controls, weeks, team_size, hours_per_person_per_week=5):
    """When the full scope is not green, offer honest reduced-scope tiers and
    show the feasibility of each. Returns [] when the full scope is green."""
    full = feasibility(_total_hours(controls), weeks, team_size, hours_per_person_per_week)
    if full["light"] == "green":
        return []
    tiers = [
        ("Critical only", {"critical"}),
        ("Critical + high", {"critical", "high"}),
    ]
    options = []
    for name, keep in tiers:
        subset = [c for c in controls if c["priority"] in keep]
        if not subset:
            continue
        options.append({
            "name": name,
            "control_ids": [c["id"] for c in prioritize(subset)],
            "effort_hours": _total_hours(subset),
            "feasibility": feasibility(_total_hours(subset), weeks, team_size, hours_per_person_per_week),
        })
    return options
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: PASS (9 passed).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(workplan): honest scope-reduction tiers (gap #2)"
```

---

### Task 5: Framework templates (gap #4)

**Files:**
- Create: `skills/audit-workplan-generator/reference/frameworks/soc2.json`
- Create: `skills/audit-workplan-generator/reference/frameworks/iso27001.json`
- Create: `skills/audit-workplan-generator/reference/frameworks/hipaa.json`
- Modify: `skills/audit-workplan-generator/scripts/workplan.py` (add `load_framework`)
- Test: `skills/audit-workplan-generator/tests/test_workplan.py`

- [ ] **Step 1: Write the failing test**

```python
# append to test_workplan.py
import pytest

@pytest.mark.parametrize("name,expected_fw", [
    ("soc2", "SOC 2"), ("iso27001", "ISO 27001"), ("hipaa", "HIPAA"),
])
def test_load_framework_returns_controls(name, expected_fw):
    fw = workplan.load_framework(name)
    assert fw["framework"] == expected_fw
    assert len(fw["controls"]) >= 8
    assert any(c["priority"] == "critical" for c in fw["controls"])
    for c in fw["controls"]:
        assert set(c) >= {"id", "name", "objective", "priority", "effort_hours", "evidence_examples"}
        assert c["priority"] in {"critical", "high", "medium", "low"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: FAIL — missing `load_framework` and/or reference files.

- [ ] **Step 3: Create the reference data + loader**

Create `reference/frameworks/soc2.json` (SOC 2 Trust Services common criteria — representative, real; expand later following this exact schema):

```json
{
  "framework": "SOC 2",
  "version": "2017 TSC (rev. 2022)",
  "controls": [
    {"id": "CC1.1", "name": "Control environment & integrity", "objective": "Demonstrate commitment to integrity and ethical values", "priority": "high", "effort_hours": 8, "evidence_examples": ["code of conduct", "org chart", "board minutes"]},
    {"id": "CC2.1", "name": "Communication of policies", "objective": "Internal communication of security objectives and responsibilities", "priority": "medium", "effort_hours": 6, "evidence_examples": ["published policies", "acknowledgement records"]},
    {"id": "CC5.2", "name": "Change management", "objective": "Changes to infrastructure and software are authorized, tested, and approved", "priority": "critical", "effort_hours": 20, "evidence_examples": ["change tickets with approvals", "CI/CD config", "PR review records"]},
    {"id": "CC6.1", "name": "Logical access controls", "objective": "Restrict logical access to authorized users", "priority": "critical", "effort_hours": 20, "evidence_examples": ["MFA configuration export", "SSO policy", "access control list"]},
    {"id": "CC6.2", "name": "Access provisioning & deprovisioning", "objective": "Register and authorize new users; remove access on termination", "priority": "critical", "effort_hours": 16, "evidence_examples": ["onboarding tickets", "termination checklist", "access removal logs"]},
    {"id": "CC6.3", "name": "Access reviews", "objective": "Periodically review user access rights", "priority": "high", "effort_hours": 12, "evidence_examples": ["quarterly access review records", "reviewer sign-off"]},
    {"id": "CC6.6", "name": "Encryption in transit", "objective": "Protect data transmitted over public networks", "priority": "critical", "effort_hours": 10, "evidence_examples": ["TLS configuration", "SSL Labs report"]},
    {"id": "CC6.7", "name": "Encryption at rest", "objective": "Protect data at rest", "priority": "high", "effort_hours": 10, "evidence_examples": ["database encryption settings", "KMS key policy"]},
    {"id": "CC7.2", "name": "Security monitoring", "objective": "Monitor systems to detect anomalies and security events", "priority": "high", "effort_hours": 18, "evidence_examples": ["SIEM/log-alerting config", "sample alerts"]},
    {"id": "CC7.3", "name": "Incident response", "objective": "Evaluate and respond to security incidents", "priority": "high", "effort_hours": 14, "evidence_examples": ["incident response plan", "post-incident reviews"]},
    {"id": "CC8.1", "name": "Vulnerability management", "objective": "Identify and remediate vulnerabilities", "priority": "high", "effort_hours": 16, "evidence_examples": ["scan reports", "remediation tracker", "pentest report"]},
    {"id": "A1.2", "name": "Availability / backups & DR", "objective": "Maintain backups and recovery capability", "priority": "medium", "effort_hours": 12, "evidence_examples": ["backup config", "DR test results"]},
    {"id": "C1.1", "name": "Confidentiality handling", "objective": "Identify and protect confidential information", "priority": "medium", "effort_hours": 8, "evidence_examples": ["data classification policy", "retention schedule"]}
  ]
}
```

Create `reference/frameworks/iso27001.json`:

```json
{
  "framework": "ISO 27001",
  "version": "2022 Annex A",
  "controls": [
    {"id": "A.5.1", "name": "Policies for information security", "objective": "Define and approve an information security policy set", "priority": "high", "effort_hours": 8, "evidence_examples": ["approved ISMS policy", "review records"]},
    {"id": "A.5.9", "name": "Inventory of assets", "objective": "Maintain an inventory of information and assets", "priority": "medium", "effort_hours": 10, "evidence_examples": ["asset register"]},
    {"id": "A.5.15", "name": "Access control", "objective": "Establish access control based on business requirements", "priority": "critical", "effort_hours": 20, "evidence_examples": ["access control policy", "RBAC matrix"]},
    {"id": "A.5.18", "name": "Access rights review", "objective": "Provision, review, and remove access rights", "priority": "critical", "effort_hours": 14, "evidence_examples": ["joiner/mover/leaver records", "access review"]},
    {"id": "A.5.23", "name": "Cloud services security", "objective": "Manage information security in use of cloud services", "priority": "high", "effort_hours": 10, "evidence_examples": ["cloud config baseline", "shared-responsibility mapping"]},
    {"id": "A.6.3", "name": "Security awareness & training", "objective": "Provide security awareness education", "priority": "medium", "effort_hours": 6, "evidence_examples": ["training completion records"]},
    {"id": "A.8.8", "name": "Technical vulnerability management", "objective": "Manage technical vulnerabilities", "priority": "high", "effort_hours": 16, "evidence_examples": ["scan reports", "patch records"]},
    {"id": "A.8.9", "name": "Configuration management", "objective": "Establish and maintain secure configurations", "priority": "high", "effort_hours": 12, "evidence_examples": ["hardening baselines", "IaC config"]},
    {"id": "A.8.15", "name": "Logging", "objective": "Produce and protect logs of events", "priority": "high", "effort_hours": 12, "evidence_examples": ["logging config", "sample logs"]},
    {"id": "A.8.24", "name": "Use of cryptography", "objective": "Define and implement cryptographic controls", "priority": "critical", "effort_hours": 12, "evidence_examples": ["crypto policy", "TLS and at-rest encryption evidence"]},
    {"id": "A.5.24", "name": "Incident management planning", "objective": "Plan and prepare for incident management", "priority": "high", "effort_hours": 14, "evidence_examples": ["incident response plan"]},
    {"id": "A.5.30", "name": "ICT readiness for continuity", "objective": "Plan ICT continuity and recovery", "priority": "medium", "effort_hours": 12, "evidence_examples": ["BCP/DR plan", "DR test results"]}
  ]
}
```

Create `reference/frameworks/hipaa.json`:

```json
{
  "framework": "HIPAA",
  "version": "Security Rule (45 CFR 164.3xx)",
  "controls": [
    {"id": "164.308(a)(1)", "name": "Security management process / risk analysis", "objective": "Conduct an accurate risk analysis and manage risk", "priority": "critical", "effort_hours": 20, "evidence_examples": ["risk analysis", "risk management plan"]},
    {"id": "164.308(a)(3)", "name": "Workforce access management", "objective": "Authorize and supervise workforce access to ePHI", "priority": "critical", "effort_hours": 16, "evidence_examples": ["access authorization records", "termination procedures"]},
    {"id": "164.308(a)(4)", "name": "Information access management", "objective": "Policies for granting access to ePHI", "priority": "high", "effort_hours": 12, "evidence_examples": ["access control policy", "RBAC"]},
    {"id": "164.308(a)(5)", "name": "Security awareness & training", "objective": "Security awareness and training program", "priority": "medium", "effort_hours": 6, "evidence_examples": ["training records"]},
    {"id": "164.308(a)(6)", "name": "Security incident procedures", "objective": "Identify and respond to security incidents", "priority": "high", "effort_hours": 12, "evidence_examples": ["incident response plan", "incident log"]},
    {"id": "164.308(a)(7)", "name": "Contingency plan", "objective": "Data backup, disaster recovery, emergency mode", "priority": "high", "effort_hours": 14, "evidence_examples": ["backup plan", "DR test"]},
    {"id": "164.308(b)(1)", "name": "Business associate agreements", "objective": "Obtain satisfactory assurances from business associates", "priority": "critical", "effort_hours": 10, "evidence_examples": ["BAA inventory", "signed BAAs"]},
    {"id": "164.312(a)(1)", "name": "Access control (technical)", "objective": "Unique user IDs, automatic logoff, encryption", "priority": "critical", "effort_hours": 16, "evidence_examples": ["unique ID config", "session timeout settings", "encryption settings"]},
    {"id": "164.312(b)", "name": "Audit controls", "objective": "Record and examine activity in systems with ePHI", "priority": "high", "effort_hours": 12, "evidence_examples": ["audit log config", "EHR audit trails"]},
    {"id": "164.312(e)(1)", "name": "Transmission security", "objective": "Protect ePHI transmitted over networks", "priority": "critical", "effort_hours": 10, "evidence_examples": ["TLS config", "VPN config"]}
  ]
}
```

Add the loader to `workplan.py`:

```python
# append to workplan.py
_REF_DIR = pathlib.Path(__file__).resolve().parents[1] / "reference" / "frameworks"
_ALIASES = {"soc2": "soc2", "soc 2": "soc2", "iso27001": "iso27001", "iso 27001": "iso27001", "hipaa": "hipaa"}


def load_framework(name):
    """Load a bundled framework control template by name (case/space-insensitive)."""
    key = _ALIASES.get(name.strip().lower())
    if not key:
        raise ValueError(f"Unknown framework {name!r}. Known: {sorted(set(_ALIASES.values()))}")
    return json.loads((_REF_DIR / f"{key}.json").read_text())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: PASS (12 passed — 3 parametrized + prior 9).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(workplan): bundled SOC2/ISO27001/HIPAA framework templates (gap #4)"
```

---

### Task 6: Cost ranges (gap #5)

**Files:**
- Create: `skills/audit-workplan-generator/reference/cost-ranges.json`
- Modify: `skills/audit-workplan-generator/scripts/workplan.py` (add `cost_estimate`)
- Test: `skills/audit-workplan-generator/tests/test_workplan.py`

- [ ] **Step 1: Write the failing test**

```python
# append to test_workplan.py
def test_cost_estimate_includes_all_in_and_hidden_warning():
    est = workplan.cost_estimate()
    assert est["implementation_advisory_usd"] == [10000, 25000]
    assert est["independent_audit_usd"] == [10000, 50000]
    assert est["underestimate_warning_pct"] == [30, 50]
    assert "source" in est
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: FAIL — missing `cost_estimate`.

- [ ] **Step 3: Write implementation + data**

Create `reference/cost-ranges.json` (figures are the verified ranges from the Axis GRC pain research, 2026-10-11 — do not alter without a new source):

```json
{
  "source": "Axis GRC & Compliance Pain Research, 2026-10-11 (adversarially verified)",
  "implementation_advisory_usd": [10000, 25000],
  "independent_audit_usd": [10000, 50000],
  "underestimate_warning_pct": [30, 50],
  "renewal_trap_note": "Year-1 startup discounts (up to ~70% off) can revert to list at renewal once you're locked in via evidence history/integrations; budget for a 20-40% Year-2 increase and watch the 30-day auto-renewal notice window.",
  "per_framework_tax_note": "Each additional framework on major platforms can add ~$5K/yr; costs escalate past 3 frameworks."
}
```

Add to `workplan.py`:

```python
# append to workplan.py
def cost_estimate():
    """Return the sourced all-in external cost ranges. Never invent numbers:
    these come from reference/cost-ranges.json and must cite their source."""
    path = pathlib.Path(__file__).resolve().parents[1] / "reference" / "cost-ranges.json"
    return json.loads(path.read_text())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: PASS (13 passed).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(workplan): sourced all-in cost ranges (gap #5)"
```

---

### Task 7: build_workplan orchestrator

**Files:**
- Modify: `skills/audit-workplan-generator/scripts/workplan.py`
- Test: `skills/audit-workplan-generator/tests/test_workplan.py`

- [ ] **Step 1: Write the failing test**

```python
# append to test_workplan.py
def test_build_workplan_end_to_end_from_framework():
    plan = workplan.build_workplan(framework="soc2", weeks=16, team_size=3, concerns=["encryption", "change management"])
    assert plan["framework"] == "SOC 2"
    assert plan["control_count"] >= 8
    assert set(plan) >= {"framework", "control_count", "feasibility", "phases", "monday_top3", "scope_options", "cost_estimate", "disclaimer"}
    assert len(plan["monday_top3"]) == 3
    assert plan["feasibility"]["light"] in {"green", "yellow", "red"}
    # honesty: a disclaimer is always present
    assert "estimate" in plan["disclaimer"].lower()


def test_build_workplan_accepts_explicit_controls():
    controls = _sample_controls()
    plan = workplan.build_workplan(controls=controls, weeks=2, team_size=1)
    assert plan["control_count"] == 4
    assert plan["feasibility"]["light"] == "red"
    assert plan["scope_options"]  # tight timeline -> options offered
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: FAIL — missing `build_workplan`.

- [ ] **Step 3: Write implementation**

```python
# append to workplan.py
_DISCLAIMER = (
    "This is an estimate, not a guarantee. Effort hours assume compliance side-work "
    "(~5 hrs/person/week), not full-time staff. Cost ranges are sourced (see cost_estimate.source). "
    "A green light means the numbers work, not that the audit will pass — that depends on the work you do."
)


def build_workplan(framework=None, controls=None, weeks=16, team_size=3, concerns=None, hours_per_person_per_week=5):
    """Top-level entry point used by SKILL.md. Provide either a bundled
    `framework` name or an explicit `controls` list."""
    if controls is None:
        if not framework:
            raise ValueError("Provide either `framework` or `controls`.")
        controls = load_framework(framework)["controls"]
        framework_name = load_framework(framework)["framework"]
    else:
        framework_name = framework or "custom"
    required = _total_hours(controls)
    return {
        "framework": framework_name,
        "control_count": len(controls),
        "feasibility": feasibility(required, weeks, team_size, hours_per_person_per_week),
        "phases": phase_plan(controls, weeks),
        "monday_top3": [{"id": c["id"], "name": c["name"]} for c in monday_top3(controls)],
        "scope_options": scope_options(controls, weeks, team_size, hours_per_person_per_week),
        "cost_estimate": cost_estimate(),
        "disclaimer": _DISCLAIMER,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: PASS (15 passed).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(workplan): build_workplan orchestrator with honesty disclaimer"
```

---

### Task 8: CLI entry + Markdown rendering

**Files:**
- Modify: `skills/audit-workplan-generator/scripts/workplan.py` (add `render_markdown` + `__main__`)
- Test: `skills/audit-workplan-generator/tests/test_workplan.py`

- [ ] **Step 1: Write the failing test**

```python
# append to test_workplan.py
def test_render_markdown_contains_traffic_light_and_top3():
    plan = workplan.build_workplan(framework="soc2", weeks=16, team_size=3)
    md = workplan.render_markdown(plan)
    assert "# SOC 2 Audit Prep Workplan" in md
    assert any(flag in md for flag in ("🟢", "🟡", "🔴"))
    assert "Start Monday" in md
    assert "estimate" in md.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: FAIL — missing `render_markdown`.

- [ ] **Step 3: Write implementation**

```python
# append to workplan.py
_LIGHT_EMOJI = {"green": "🟢", "yellow": "🟡", "red": "🔴"}


def render_markdown(plan):
    f = plan["feasibility"]
    lines = [
        f"# {plan['framework']} Audit Prep Workplan",
        "",
        f"**Feasibility:** {_LIGHT_EMOJI[f['light']]} {f['verdict']}",
        f"(needs ~{f['required_hours']}h, you have ~{f['available_hours']}h at this capacity)",
        "",
        "## Start Monday (top 3)",
    ]
    lines += [f"- **{c['id']}** — {c['name']}" for c in plan["monday_top3"]]
    lines += ["", "## Phases"]
    for p in plan["phases"]:
        lines.append(f"### Phase {p['phase']}: {p['name']} (weeks {p['weeks']}, ~{p['effort_hours']}h)")
        lines.append(", ".join(p["control_ids"]) or "_(none)_")
    if plan["scope_options"]:
        lines += ["", "## If the timeline is tight, consider:"]
        for o in plan["scope_options"]:
            lines.append(f"- **{o['name']}** ({len(o['control_ids'])} controls, ~{o['effort_hours']}h): "
                         f"{_LIGHT_EMOJI[o['feasibility']['light']]} {o['feasibility']['verdict']}")
    c = plan["cost_estimate"]
    lines += [
        "",
        "## Honest all-in cost",
        f"- Implementation / advisory: ${c['implementation_advisory_usd'][0]:,}–${c['implementation_advisory_usd'][1]:,}",
        f"- Independent audit: ${c['independent_audit_usd'][0]:,}–${c['independent_audit_usd'][1]:,}",
        f"- Most first-timers underestimate the all-in by {c['underestimate_warning_pct'][0]}–{c['underestimate_warning_pct'][1]}%.",
        f"- _{c['source']}_",
        "",
        f"> {plan['disclaimer']}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Generate an honest audit prep workplan.")
    ap.add_argument("--framework", help="soc2 | iso27001 | hipaa")
    ap.add_argument("--weeks", type=int, default=16)
    ap.add_argument("--team-size", type=int, default=3)
    ap.add_argument("--concerns", default="", help="comma-separated keywords")
    ap.add_argument("--format", choices=["json", "md"], default="md")
    a = ap.parse_args()
    plan = build_workplan(
        framework=a.framework, weeks=a.weeks, team_size=a.team_size,
        concerns=[c.strip() for c in a.concerns.split(",") if c.strip()],
    )
    print(json.dumps(plan, indent=2) if a.format == "json" else render_markdown(plan))
```

- [ ] **Step 4: Run test to verify it passes + smoke-test the CLI**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/test_workplan.py -q`
Expected: PASS (16 passed).
Run: `python skills/audit-workplan-generator/scripts/workplan.py --framework soc2 --weeks 6 --team-size 1 --concerns encryption`
Expected: Markdown with a 🔴 or 🟡 light and scope options.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(workplan): markdown rendering + CLI entry point"
```

---

### Task 9: Update SKILL.md to wire in the five gaps + honesty framing

**Files:**
- Modify: `skills/audit-workplan-generator/SKILL.md`

- [ ] **Step 1: Edit SKILL.md**

Make these concrete changes (the file already describes the skill; these additions wire in the new capabilities):
1. Under "Key Features", add a **Feasibility traffic-light** subsection: the skill must call `workplan.feasibility()` and report 🟢/🟡/🔴 honestly — never soften a 🔴.
2. Add a **Scope reduction** subsection: when not green, present `scope_options()` tiers before anything else.
3. Add **Monday-morning top-3**: every response ends with "Start Monday (top 3)".
4. Add **Framework templates**: when the user has no spreadsheet, call `load_framework("soc2"|"iso27001"|"hipaa")`.
5. Add **Honest cost**: always include `cost_estimate()` ranges with their source; never invent figures.
6. Add a **How this skill runs** section documenting the entry point: `python scripts/workplan.py --framework <fw> --weeks N --team-size N --concerns "a,b"` (or import `build_workplan`).
7. Add a top-of-file **Honesty contract**: "This skill never claims a timeline is achievable when the capacity math says otherwise, and never invents costs or evidence."

- [ ] **Step 2: Verify the skill frontmatter is valid**

Run: `head -12 skills/audit-workplan-generator/SKILL.md`
Expected: YAML frontmatter with `name:` and `description:` intact.

- [ ] **Step 3: Commit**

```bash
git add skills/audit-workplan-generator/SKILL.md
git commit -m "docs(workplan): wire SKILL.md to the five gap features + honesty contract"
```

---

### Task 10: Skill README + full-suite green

**Files:**
- Create: `skills/audit-workplan-generator/README.md`

- [ ] **Step 1: Write the README**

Cover: one-line purpose, the honesty contract, how to run (CLI + import), the three bundled frameworks, example output (paste a short rendered Markdown sample from the Task 8 smoke test), and "what it deliberately will not do" (fabricate costs, promise an unrealistic timeline).

- [ ] **Step 2: Run the whole test suite**

Run: `. .venv/bin/activate && pytest skills/audit-workplan-generator/tests/ -q`
Expected: PASS (16 passed), zero failures.

- [ ] **Step 3: Commit**

```bash
git add skills/audit-workplan-generator/README.md
git commit -m "docs(workplan): skill README with example output"
```

---

## Self-review (completed during planning)

- **Spec coverage:** all five gaps map to tasks — feasibility (T2), scope reduction (T4), Monday-morning top-3 (T3), framework templates (T5), cost ranges (T6). Orchestration (T7), rendering/CLI (T8), SKILL.md wiring (T9), README (T10). ✅
- **Placeholder scan:** reference data is real (not "TODO"); every code step has complete code. Framework templates are representative seeds (8–13 controls each) with a documented schema for later expansion — not placeholders. ✅
- **Type consistency:** control dict keys (`id/name/objective/priority/effort_hours/evidence_examples`) and `feasibility()` return keys (`required_hours/available_hours/ratio/light/verdict`) are identical across all tasks. ✅
