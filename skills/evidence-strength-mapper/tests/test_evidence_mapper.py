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


def test_render_markdown_leads_with_weak_pct_and_upgrades():
    controls = [{"id": "C1", "name": "Access", "evidence_examples": ["Screenshot of MFA settings"]}]
    md = em.render_markdown(em.strength_report(controls))
    assert "Substance, not screenshots" in md
    assert "%" in md
    assert "Replace with" in md  # upgrade guidance for the weak item
