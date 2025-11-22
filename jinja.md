DEVPLAN_FOR_NEXT_AGENT — Jinja Coverage Upgrade

You are an AI coding agent.
Goal: make Devussy’s Jinja templates use more of the JSON the pipeline already produces, without blowing up tokens or breaking existing flows.

0. Operating Rules (read once)

Read only what you need:

This file

README (pipeline overview)

The Jinja templates under templates/

The Python that builds Jinja contexts & renders templates.

Follow the existing handoff protocol in HANDOFF.md:

Do one phase at a time.

Verify work.

Update docs and HANDOFF.md before you stop.

1. Map Templates & Contexts

Goal: For each Jinja template, know exactly which context it gets and what it uses.

Inputs

templates/ directory

Jinja environment / render calls in src/

Tasks

 Find all Jinja renders: search for Environment, .get_template(, .render(.

 List all templates actually used in the pipeline (Design, DevPlan, Handoff, per-phase, etc.).

 For each render call, log the full context to JSON (dev-only):

Write to DevDocs/JINJA_DATA_SAMPLES/<stage>.json or similar.

 For each template, list all variables/structures used:

{{ ... }}, {% for %}, {% if %}, etc.

Outputs

 DevDocs/JINJA_CONTEXT_MAP.md

For each template:

Which render call(s) feed it

Context keys it receives

Context keys it actually uses

Done when

Every template that is rendered by the pipeline appears in JINJA_CONTEXT_MAP.md with a list of used keys and a sample JSON context file.

2. Gap Analysis (JSON vs Rendered Output)

Goal: Find valuable data the LLM already produced that never shows up (or shows up weakly) in the docs.

Inputs

DevDocs/JINJA_CONTEXT_MAP.md

JSON samples in DevDocs/JINJA_DATA_SAMPLES/

Tasks

 For each stage (Design, DevPlan, Handoff):

Compare JSON context keys vs keys used in the template.

Mark keys as used, partially_used, or unused.

 Focus on high-signal stuff:

Updated requirements vs original

Constraints / non-goals

Tech changes / stack choices

Risks & mitigations

Notes / rationale from design review

Repo analysis / runtime config / LLM config

 For each unused or partially_used key, propose how to surface it:

New section, table, bullet list, checklist, etc.

Outputs

 DevDocs/JINJA_GAPS.md

Per stage/template: list of unused/underused keys + short proposal for how to render them.

Done when

Every major context key is either:

Used in a template, or

Listed in JINJA_GAPS.md with a concrete “how to show this” note.

3. Template Upgrade & Shared Macros

Goal: Upgrade templates to surface the important data in a clean, reusable, token-aware way.

Inputs

Current templates

DevDocs/JINJA_GAPS.md

Tasks

 Create templates/_shared_macros.jinja with macros for:

Project header block

Constraints / non-goals

Risks & mitigations

Tech / stack decisions

LLM + runtime config summary

DevPlan phases & tasks (goal, steps, acceptance criteria, deps)

 Refactor Design template:

Ensure sections for:

Project summary

Architecture / components

Constraints & non-goals

Tech choices / changes

Risks & mitigations

Notes / rationale from design review

Use macros + {% if %} blocks so missing data doesn’t break render.

 Refactor DevPlan template(s):

Devplan overview

Per-phase chunks with:

Goal

Tasks / steps

Dependencies

Acceptance criteria

 Refactor Handoff template:

Minimal but complete:

Links/pointers to design / devplan docs

Key constraints + risks

LLM + runtime config snapshot

Repo / test setup summary

Open questions / TODOs

 Add a detail_level context key ("short" | "normal" | "verbose") and guard optional verbose sections with {% if detail_level != "short" %} etc.

Outputs

 Updated templates using macros in _shared_macros.jinja

 DevDocs/TEMPLATE_DESIGN_NOTES.md describing:

Sections per template

Which macros they use

How detail_level affects output

Done when

Design, DevPlan, and Handoff docs render richer sections (constraints, risks, tech, etc.) from the existing JSON, without breaking when some fields are missing.

4. Context-Builder Updates

Goal: Ensure Python context builders actually populate the fields the templates expect.

Inputs

Updated templates/macros

Existing Python that prepares Jinja context

Tasks

 For each stage, define a compact schema in code comments / docs, e.g.:

design_context.project, design_context.design_summary.risks[], ...constraints[], ...tech_changes[], ...notes

devplan_context.phases[] (id, name, goal, tasks[], deps, acceptance_criteria)

handoff_context.project, ...links, ...open_questions, ...llm_config, ...runtime_config

 Normalize raw LLM JSON into these schemas:

Map existing fields; don’t introduce new model calls.

 Provide safe defaults for optional fields ([], "", None) so Jinja conditionals handle them.

 (Optional) Add a small helper that logs unused context keys per template in debug mode to guide future coverage improvements.

 Thread detail_level from config/CLI into the context for each stage.

Outputs

 Updated context-building functions in src/ that match the new schemas.

 DevDocs/JINJA_CONTEXT_SCHEMA.md summarizing the schema per stage.

Done when

All templates render without errors using the live pipeline.

Core sections (constraints, risks, tech, phases, acceptance criteria, config) are consistently populated when the LLM provides them.

5. Tests & Golden Outputs

Goal: Lock in behavior so future changes don’t silently break coverage.

Inputs

New templates

New context builders

Tasks

 Create JSON fixtures:

tests/fixtures/design_context_full.json

tests/fixtures/devplan_context_full.json

tests/fixtures/handoff_context_full.json

 Create golden markdown outputs for those fixtures:

tests/fixtures/design_expected.md

tests/fixtures/devplan_expected.md

tests/fixtures/handoff_expected.md

 Add tests that:

Load fixture JSON

Render templates via the same Jinja setup as production

Compare against golden files (strict or line-based; your choice).

 Add a fast smoke test that runs the full pipeline on a tiny toy project and asserts:

All expected docs get generated

Key headings/sections exist.

Outputs

 New tests under tests/ for templates + pipeline smoke test.

Done when

pytest (or your test runner) passes and will fail clearly if:

A template section is removed

A key field disappears from the rendered docs.

6. Final Handoff Update

Goal: Hand back a clean, low-friction state for the next agent / human.

Tasks

 Update HANDOFF.md with:

Short summary of what changed in the Jinja/template system.

Where to find:

JINJA_CONTEXT_MAP.md

JINJA_GAPS.md

JINJA_CONTEXT_SCHEMA.md

TEMPLATE_DESIGN_NOTES.md

Template tests and fixtures.

A quick recipe: “How to add a new field end-to-end”.

 Note any leftovers or nice-to-have improvements.

Done when

A new agent can:

Read HANDOFF.md + the DevDocs mentioned above

Understand the template system

Safely extend coverage without rereading the whole codebase.