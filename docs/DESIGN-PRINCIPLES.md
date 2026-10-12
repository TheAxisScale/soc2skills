# Design Principles — How to build an honest compliance tool

Most compliance software optimizes for what's easy to screenshot, not what actually
keeps customers safe. These are the principles we hold every skill in this kit to.
They're here in the open so you can hold us to them — and reuse them if you build
your own.

## 1. Never fabricate

A compliance tool that invents status, evidence, costs, or audit outcomes is worse
than no tool — it manufactures false confidence. Our skills:

- State estimates **as estimates**, and show the assumptions behind them.
- Cite every number. Cost ranges and statistics trace to a dated source (see each
  skill's `reference/` data), never to a confident guess.
- Never claim a control is met, evidence exists, or an audit will pass.

## 2. Form beats content (for evidence)

A screenshot *of a configuration export* is still a screenshot. The weakness lives
in the **form** of the evidence — a single screen, at a single moment, chosen by
the person being audited — not in its subject. So we classify evidence by how it's
produced:

- **Strong** — pulled from the system of record: config exports, automated logs,
  API pulls, tickets/PRs with approvals, independent or tool-generated reports.
- **Weak** — screenshots, self-authored documents, and manual assertions. They can
  prove a document exists; they rarely prove a control *operated*.

When in doubt, evidence is treated as **weak until it can be tied to a system of
record** — never the other way around.

## 3. Deterministic core, honest math

Every recommendation that can be computed is computed in tested code, so it's
reproducible and can't be quietly softened by an optimistic narrator.

- Feasibility is arithmetic: required hours vs. realistic capacity. If the numbers
  say a timeline is unrealistic, the tool says **red** — it does not round up to
  "achievable."
- The logic is unit-tested (see each skill's `tests/`). The prose layer explains
  the result; it doesn't overrule it.

## 4. Sourced data only

Framework templates, cost ranges, and the evidence taxonomy are data files with
citations, not prompt-embedded lore. Change the data, and you change the output —
transparently, with a traceable source. No figure ships without one.

## 5. Helpers, not oracles

These skills run **once** to help a human do real work faster. They are not
continuous monitors, they don't replace an auditor, and they don't make the
compliance decision for you. They hand you a clearer starting point and tell you
the truth about where you stand.

## What these tools deliberately will *not* do

- Call weak evidence "strong" to make you feel ready.
- Promise a timeline the capacity math doesn't support.
- Invent a cost, a control status, or an audit result.
- Auto-generate your policies and imply the work is done.

---

*These principles are the product. If a skill here ever violates one, that's a bug —
open an issue.*
