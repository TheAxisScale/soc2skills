"""Deterministic all-in compliance cost estimator. Pure stdlib. Every figure is
sourced from reference/cost-model.json; tooling is never invented."""
import json, pathlib
_MODEL = pathlib.Path(__file__).resolve().parents[1] / "reference" / "cost-model.json"

def load_model():
    return json.loads(_MODEL.read_text())

def estimate(frameworks, tooling_annual=None):
    if not frameworks:
        raise ValueError("Provide at least one framework.")
    m = load_model()
    n = len(frameworks)
    impl = list(m["implementation_advisory_usd"])
    audit = [m["independent_audit_per_framework_usd"][0] * n, m["independent_audit_per_framework_usd"][1] * n]
    tax = m["per_framework_tax_usd"] * (n - 1)
    tooling = list(tooling_annual) if tooling_annual else None
    lo = impl[0] + audit[0] + tax + (tooling[0] if tooling else 0)
    hi = impl[1] + audit[1] + tax + (tooling[1] if tooling else 0)
    return {
        "frameworks": frameworks,
        "line_items": {
            "implementation_advisory_usd": impl,
            "independent_audit_usd": audit,
            "per_framework_tax_usd": tax,
            "tooling_usd": tooling,
        },
        "total_usd": [lo, hi],
        "warnings": {
            "underestimate_pct": m["underestimate_pct"],
            "year2_increase_pct": m["year2_increase_pct"],
            "renewal_trap_note": m["renewal_trap_note"],
            "per_framework_tax_note": m["per_framework_tax_note"],
        },
        "source": m["source"],
        "disclaimer": ("This is an estimate, not a quote. Ranges are sourced (see 'source'); "
                       "tooling price is yours to supply, never invented. Most first-timers "
                       f"underestimate the all-in by {m['underestimate_pct'][0]}-{m['underestimate_pct'][1]}%."),
    }

def _usd(r): return f"${r[0]:,}-${r[1]:,}"

def render_markdown(e):
    li = e["line_items"]
    lines = [
        f"# All-in compliance cost — {', '.join(e['frameworks'])}",
        "",
        f"**All-in total: {_usd(e['total_usd'])}**",
        "",
        "## Line items",
        f"- Implementation / advisory: {_usd(li['implementation_advisory_usd'])}",
        f"- Independent audit: {_usd(li['independent_audit_usd'])}",
        f"- Per-framework tax: ${li['per_framework_tax_usd']:,}",
        f"- Tooling: {(_usd(li['tooling_usd']) if li['tooling_usd'] else 'varies — supply your quote')}",
        "",
        "## Watch out",
        f"- Most first-timers underestimate the all-in by {e['warnings']['underestimate_pct'][0]}-{e['warnings']['underestimate_pct'][1]}%.",
        f"- {e['warnings']['renewal_trap_note']}",
        f"- {e['warnings']['per_framework_tax_note']}",
        "",
        f"_{e['source']}_",
        "",
        f"> {e['disclaimer']}",
    ]
    return "\n".join(lines)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Estimate the all-in cost of a compliance program.")
    ap.add_argument("--frameworks", required=True, help="comma-separated: soc2,iso27001,hipaa")
    ap.add_argument("--tooling-low", type=int)
    ap.add_argument("--tooling-high", type=int)
    ap.add_argument("--format", choices=["json", "md"], default="md")
    a = ap.parse_args()
    tooling = [a.tooling_low, a.tooling_high] if a.tooling_low is not None and a.tooling_high is not None else None
    e = estimate([f.strip() for f in a.frameworks.split(",") if f.strip()], tooling_annual=tooling)
    print(json.dumps(e, indent=2) if a.format == "json" else render_markdown(e))

