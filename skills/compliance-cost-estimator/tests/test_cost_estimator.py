import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import cost_estimator as ce


def test_model_loads_with_sourced_ranges():
    m = ce.load_model()
    assert m["implementation_advisory_usd"] == [10000, 25000]
    assert m["independent_audit_per_framework_usd"] == [10000, 50000]
    assert m["per_framework_tax_usd"] == 5000
    assert m["year2_increase_pct"] == [20, 40]
    assert m["underestimate_pct"] == [30, 50]
    assert "Axis GRC" in m["source"]


def test_single_framework_all_in_range():
    e = ce.estimate(["soc2"])
    assert e["line_items"]["implementation_advisory_usd"] == [10000, 25000]
    assert e["line_items"]["independent_audit_usd"] == [10000, 50000]
    assert e["line_items"]["per_framework_tax_usd"] == 0
    assert e["line_items"]["tooling_usd"] is None
    assert e["total_usd"] == [20000, 75000]  # impl + audit, no tax/tooling


def test_two_frameworks_add_audit_and_tax():
    e = ce.estimate(["soc2", "iso27001"])
    assert e["line_items"]["independent_audit_usd"] == [20000, 100000]  # 2x
    assert e["line_items"]["per_framework_tax_usd"] == 5000             # 1 extra framework
    assert e["total_usd"][0] == 10000 + 20000 + 5000                    # impl_lo + audit_lo + tax


def test_tooling_included_when_supplied():
    e = ce.estimate(["soc2"], tooling_annual=[6000, 6000])
    assert e["line_items"]["tooling_usd"] == [6000, 6000]
    assert e["total_usd"] == [26000, 81000]


def test_estimate_includes_warnings_source_disclaimer():
    e = ce.estimate(["soc2"])
    w = e["warnings"]
    assert w["underestimate_pct"] == [30, 50]
    assert w["year2_increase_pct"] == [20, 40]
    assert "renewal" in w["renewal_trap_note"].lower()
    assert "Axis GRC" in e["source"]
    assert "estimate" in e["disclaimer"].lower()


def test_render_markdown_shows_total_and_warnings():
    md = ce.render_markdown(ce.estimate(["soc2", "iso27001"]))
    assert "All-in" in md
    assert "$" in md
    assert "underestimate" in md.lower()
    assert "renewal" in md.lower()
