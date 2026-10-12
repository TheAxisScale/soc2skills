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
