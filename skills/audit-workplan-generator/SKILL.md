---
name: audit-workplan-generator
description: >
  Generate comprehensive audit preparation workplans for SOC 2, SOC 1, ISO 27001, and other compliance frameworks.
  Use this whenever a user needs to prepare for an audit or compliance assessment and wants a structured plan that breaks down controls, prioritizes work, and provides actionable next steps.
  The skill takes their control list and audit context, then generates a JSON workplan (ready for app display) plus downloadable Excel checklists, priority matrices, and Q&A guides.
  Useful for: audit prep, control documentation, team coordination, progress tracking, auditor readiness.
compatibility: Excel generation (openpyxl), markdown generation, JSON output for app integration
---

# Audit Workplan Generator

Generate professional, step-by-step audit preparation plans that help teams prepare for compliance assessments (SOC 2, SOC 1, ISO 27001, etc.).

## Honesty contract (non-negotiable)

This skill **never claims a timeline is achievable when the capacity math says otherwise, and never invents costs or evidence.** Every workplan is produced by the deterministic, unit-tested core in `scripts/workplan.py`:

- A 🔴 feasibility light is reported as 🔴 — never softened to sound reassuring.
- Cost ranges are the sourced ranges from the research (`reference/cost-ranges.json`), cited with their source. No invented figures.
- A green light means *the numbers work*, not that the audit will pass — that depends on the work you do. Every output carries this disclaimer.

## What This Skill Does

This skill takes your controls/audit requirements and generates:

1. **Evidence Checklist** — Detailed list of what evidence you need for each control, with status tracking
2. **Priority Matrix** — Risk-based prioritization showing what to tackle first
3. **Weekly Workplan** — Day-by-day action plan broken into manageable tasks
4. **Auditor Q&A Guide** — Likely questions and how to answer them for your audit type
5. **Task Breakdown** — Team assignments with estimated effort per task

The output is delivered as:
- **JSON workplan** (for display in your application)
- **Excel spreadsheets** (for offline tracking and sharing)
- **Markdown documents** (for documentation and reading offline)

## When to Use

- **Audit initiation**: "We have a SOC 2 audit coming in 3 months, help us plan"
- **Framework documentation**: "I need to document these 20 controls for ISO 27001"
- **Team coordination**: "How do we organize the workload for this audit?"
- **Progress tracking**: "Show me what we need to do and how to track it"
- **Auditor preparation**: "What questions will auditors ask?"

## How to Use This Skill

### Option 1: Upload Your Controls List
Provide a spreadsheet (Excel, CSV) with your controls. Format can be flexible:
- **Simple format**: Control ID | Control Name | Description
- **Detailed format**: Control ID | Objective | Description | Evidence Required | Risk Level

The skill will parse it and generate the workplan.

**Example input:**
```
1.1, Organization Policies, Security policies are documented and reviewed annually, [...evidence...]
1.2, Organization Policies, Risk management program exists, [...evidence...]
2.1, Access Control, User access provisioned with approvals, [...evidence...]
```

### Option 2: Describe Your Audit
Tell me about your audit in natural language:
- Audit framework (SOC 2, SOC 1, ISO 27001, etc.)
- Audit timeline (when is it, how long do you have)
- Company type/context (SaaS, financial services, healthcare, etc.)
- Risk areas (what concerns you most)
- Current state (what you already have in place)

**Example:**
> "We're prepping for a SOC 2 Type II audit in 6 months. We're a SaaS company. Most concerned about access controls and change management. We have basic policies but need to document controls."

### Option 3: Upload Controls + Provide Context
Provide your controls spreadsheet AND additional context about your situation, priorities, and timeline.

## What You'll Get Back

### 1. JSON Workplan (For Your App)
Structured data your application can render as:
- Interactive timeline / Gantt chart
- Clickable checklist with progress tracking
- Priority matrix visualization
- Task assignment board
- Status dashboard

```json
{
  "audit_type": "SOC 2 Type II",
  "timeline_weeks": 24,
  "control_count": 28,
  "workplan": {
    "phases": [
      {
        "phase": "Week 1-2",
        "name": "Foundation & Documentation",
        "controls": ["1.1", "1.2", "5.1", ...],
        "effort_hours": 20,
        "tasks": [
          {
            "id": "task_1.1",
            "control_id": "1.1",
            "title": "Finalize Security Policies",
            "description": "...",
            "owner": "Security Lead",
            "due_date": "2026-06-10",
            "status": "Not Started",
            "evidence_needed": [...]
          }
        ]
      }
    ],
    "critical_controls": ["2.4", "4.4", ...],
    "risk_assessment": {...}
  }
}
```

### 2. Excel Files (For Tracking & Sharing)
- **Evidence Checklist**: Control ID | Description | Evidence Required | Status | Owner | Due Date
- **Priority Matrix**: Control | Risk Level | Effort | Days to Complete | Current Status
- **Weekly Tracker**: Phase | Target | Completed | On Track | Notes

### 3. Markdown Documents (For Reading & Documentation)
- **Quick Start Guide**: 3-week plan with priorities
- **Auditor Q&A**: Common questions and sample answers
- **Evidence Organization**: Folder structure template
- **Control Summaries**: Objective-by-objective breakdown

## How this skill runs

All decision logic lives in the tested Python core. Call it one of two ways:

```bash
# CLI (Markdown by default; --format json for app integration)
python scripts/workplan.py --framework soc2 --weeks 16 --team-size 3 --concerns "encryption,change management"
```

```python
# or import directly
from workplan import build_workplan, render_markdown
plan = build_workplan(framework="soc2", weeks=16, team_size=3, concerns=["encryption"])
print(render_markdown(plan))
```

`build_workplan` accepts either a bundled `framework` name or an explicit `controls` list.

## Key Features

### Feasibility traffic-light (gap #1)
The skill **must** call `workplan.feasibility()` and report 🟢 / 🟡 / 🔴 honestly. Thresholds: capacity ratio ≤ 0.8 → 🟢, ≤ 1.0 → 🟡 (tight), otherwise 🔴 (unrealistic). Capacity assumes ~5 hrs/person/week of compliance side-work, not full-time staff. **Never soften a 🔴.**

### Scope reduction (gap #2)
When feasibility is **not** green, present `workplan.scope_options()` tiers (Critical only; Critical + high) — with each tier's own feasibility light — *before* anything else, so the team sees an honest achievable path instead of a fantasy timeline.

### Monday-morning top-3 (gap #3)
Every response ends with a **"Start Monday (top 3)"** section: the three highest-priority controls to begin this week, from `workplan.monday_top3()`.

### Framework templates (gap #4)
When the user has no spreadsheet, call `workplan.load_framework("soc2" | "iso27001" | "hipaa")` to seed the workplan from a bundled control template (`reference/frameworks/*.json`).

### Honest cost (gap #5)
Always include `workplan.cost_estimate()` ranges with their source. These come from `reference/cost-ranges.json`; **never invent figures.** Flag that most first-timers underestimate the all-in cost by 30–50%.

### Risk-Based Prioritization
Controls are automatically prioritized based on:
- Risk to audit success (critical vs. medium vs. low)
- Effort required to evidence
- Dependencies on other controls
- Your stated concerns and priorities

### Flexible Inputs
- Works with partial information — provide what you have, we'll ask for clarification
- Adapts to your company type (SaaS, financial, healthcare, startup, enterprise)
- Handles multiple frameworks (SOC 2, SOC 1, ISO 27001, etc.)
- Learns from context clues in your documents

### Team-Friendly Format
- Clear ownership and assignments
- Realistic time estimates
- Dependency tracking
- Progress visibility

### Auditor-Ready
- Sample Q&A for common auditor questions
- Evidence organization templates
- Likely exceptions and how to handle them
- Framework-specific guidance

## Common Scenarios

### "I have controls but don't know where to start"
Provide your controls list and we'll:
1. Assess each control's evidence requirement
2. Prioritize by risk and effort
3. Create a day-by-day plan
4. Assign to team members

### "I'm starting from scratch"
Describe your audit type, company, and concerns. We'll:
1. Generate recommended control list
2. Map to your business context
3. Create full workplan
4. Suggest implementation approach

### "I have 2 months, not 6 months"
Provide your constraints and we'll:
1. Identify critical-path controls
2. Parallelize what's possible
3. Flag realistic vs. unrealistic timelines
4. Suggest scope reduction if needed

### "I need to brief my team"
We'll generate:
1. Summary of what's needed
2. Task assignments with effort
3. Timeline and dependencies
4. Team communication template

## Technical Notes

The skill generates:
- **JSON** for app integration and real-time tracking
- **Excel workbooks** via openpyxl (detailed checklists, matrices, trackers)
- **Markdown files** for documentation and sharing
- **HTML** (optional) for pretty formatted output

All outputs are ready to download, share, print, or embed in your application.

---

## What Happens Next

**Step 1**: Provide your controls (upload file or describe your audit)
**Step 2**: Clarify details about your audit context and concerns
**Step 3**: Review the workplan we generate
**Step 4**: Download files and/or integrate JSON into your app
**Step 5**: Start executing — we'll provide a day-by-day action plan

## Questions to Answer

When you use this skill, be ready to share:
- **Audit type**: SOC 2 Type II, SOC 1, ISO 27001, HIPAA, PCI-DSS, custom?
- **Timeline**: When is the audit? How long do you have?
- **Company context**: SaaS, financial, healthcare, startup, enterprise?
- **Current state**: Do you have policies, controls, monitoring in place?
- **Risk concerns**: What worries you most about audit readiness?
- **Team size**: How many people will work on this?
- **Scope**: Full audit or specific domains?

If you don't have this information, no problem — we'll work through it together.

---

## Example Output Structure

The workplan JSON includes:

```
{
  "metadata": {
    "audit_type": "SOC 2 Type II",
    "framework_version": "SSAE 18",
    "generated_date": "2026-05-27",
    "company_context": "SaaS, 50 people"
  },
  "timeline": {
    "audit_start": "2026-11-01",
    "weeks_available": 24,
    "critical_deadline": "2026-10-15"
  },
  "controls_summary": {
    "total_controls": 28,
    "critical_controls": 4,
    "high_priority": 8,
    "medium_priority": 10,
    "low_priority": 6
  },
  "workplan": {
    "phases": [ ... ],
    "critical_path": [ ... ],
    "risk_matrix": { ... },
    "team_assignments": { ... }
  },
  "outputs": {
    "files_generated": ["evidence_checklist.xlsx", "priority_matrix.xlsx", "qa_guide.md", ...]
  }
}
```

Every field in the JSON is designed to be rendered in your app UI.
