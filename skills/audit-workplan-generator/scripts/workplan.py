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


_REF_DIR = pathlib.Path(__file__).resolve().parents[1] / "reference" / "frameworks"
_ALIASES = {"soc2": "soc2", "soc 2": "soc2", "iso27001": "iso27001", "iso 27001": "iso27001", "hipaa": "hipaa"}


def load_framework(name):
    """Load a bundled framework control template by name (case/space-insensitive)."""
    key = _ALIASES.get(name.strip().lower())
    if not key:
        raise ValueError(f"Unknown framework {name!r}. Known: {sorted(set(_ALIASES.values()))}")
    return json.loads((_REF_DIR / f"{key}.json").read_text())


def cost_estimate():
    """Return the sourced all-in external cost ranges. Never invent numbers:
    these come from reference/cost-ranges.json and must cite their source."""
    path = pathlib.Path(__file__).resolve().parents[1] / "reference" / "cost-ranges.json"
    return json.loads(path.read_text())


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
