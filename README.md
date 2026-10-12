# The Honest SOC 2 Starter Kit

Free, open Claude Skills for first-time SOC 2 — the honest version.

Most compliance tooling optimizes for what's easy to screenshot, not what actually
keeps customers safe. This kit is the opposite: a small set of skills that tell
founders the truth about getting audit-ready — what the work really is, what it
really costs, and which "evidence" an auditor should never accept.

No gatekeeping. No theater. Substance, not screenshots.

## Skills

| Skill | What it does |
|---|---|
| [`audit-workplan-generator`](skills/audit-workplan-generator/) | Turns a control list (or a plain-English description of your audit) into a phased, risk-prioritized prep workplan — critical controls first, realistic effort estimates, and an honest feasibility read on your timeline. |
| [`evidence-strength-mapper`](skills/evidence-strength-mapper/) | For each control, tells you what evidence proves it — and flags which evidence is **system-of-record (strong)** vs **screenshot (weak / stale / cherry-pickable)**, so you collect evidence that survives an audit. |

## Who it's for

First-time SOC 2 (and ISO 27001 / HIPAA) at startups and SMBs — the teams who've
been told compliance is "fast and easy" and are finding out otherwise.

## Using a skill

Each skill is a standard [Claude Skill](https://docs.claude.com): a `SKILL.md`
plus supporting scripts and reference data. Point Claude at the skill directory,
or copy it into your own skills folder.

Every skill also runs standalone from the command line — no setup beyond Python 3.11+:

```bash
# An honest, risk-prioritized SOC 2 prep workplan (SOC 2 / ISO 27001 / HIPAA built in)
python skills/audit-workplan-generator/scripts/workplan.py \
  --framework soc2 --weeks 16 --team-size 3 --concerns "encryption,access reviews"

# Which of your evidence is strong vs. a weak screenshot — and what to collect instead
python skills/evidence-strength-mapper/scripts/evidence_mapper.py \
  --evidence "Screenshot of MFA settings; SIEM audit log; access control policy"
```

Run the tests: `pip install pytest && pytest skills/ -q` (26 tests).

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, improve it.

## How we build

- **[Design Principles](docs/DESIGN-PRINCIPLES.md)** — the honesty rules every skill is held to.
- **[Build specs](docs/plans/)** — the complete, test-driven specifications each skill was built from. Published on purpose; audit our claims against the tests.

## Honesty guarantees

- Every cost range and statistic is sourced, not invented.
- These skills never fabricate compliance status, evidence, or audit outcomes.
- They tell you when a timeline is unrealistic instead of pretending it isn't.

---

*Built by [Axis](https://axis-scale.com). We make compliance that's true, not theater.*
