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


def test_scope_options_only_offered_when_not_green():
    controls = _sample_controls()
    # plenty of capacity -> no reduction needed
    assert workplan.scope_options(controls, weeks=16, team_size=4) == []


def test_scope_options_offer_critical_only_when_red():
    controls = _sample_controls()
    # weeks=6, team=1 -> 30h capacity: full scope (57h) stays red so options are
    # offered, while the Critical-only tier (G1+AC1 = 30h) becomes feasible.
    opts = workplan.scope_options(controls, weeks=6, team_size=1)
    assert len(opts) >= 1
    critical_only = next(o for o in opts if o["name"] == "Critical only")
    assert set(critical_only["control_ids"]) == {"G1", "AC1"}
    assert critical_only["feasibility"]["light"] in ("green", "yellow")


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


def test_cost_estimate_includes_all_in_and_hidden_warning():
    est = workplan.cost_estimate()
    assert est["implementation_advisory_usd"] == [10000, 25000]
    assert est["independent_audit_usd"] == [10000, 50000]
    assert est["underestimate_warning_pct"] == [30, 50]
    assert "source" in est


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


def test_render_markdown_contains_traffic_light_and_top3():
    plan = workplan.build_workplan(framework="soc2", weeks=16, team_size=3)
    md = workplan.render_markdown(plan)
    assert "# SOC 2 Audit Prep Workplan" in md
    assert any(flag in md for flag in ("🟢", "🟡", "🔴"))
    assert "Start Monday" in md
    assert "estimate" in md.lower()
