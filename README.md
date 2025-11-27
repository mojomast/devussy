<div align="center">

<img src="docs/assets/devussy_logo_minimal.png" alt="Devussy logo" width="100%" />

[![GitHub](https://img.shields.io/badge/repo-mojomast%2Fdevussy-181717?logo=github)](https://github.com/mojomast/devussy)
![Python](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi&logoColor=white)
![TUI](https://img.shields.io/badge/TUI-Textual-333333)
![Frontend](https://img.shields.io/badge/frontend-Next.js-000000?logo=nextdotjs&logoColor=white)
![UI](https://img.shields.io/badge/UI-Tailwind_CSS-06B6D4?logo=tailwindcss&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-brightgreen)
![Status](https://img.shields.io/badge/status-v0.4.0-blue)

# Devussy

*make it go brrrrrrrrrrrrrrrrrrrrrrrrrr*

🔗 **Live Demo:** [dev.ussy.host](https://dev.ussy.host) (limited time testing release with built-in inference)

> ⚠️ **v0.4.0 Status Note:** This release is live at dev.ussy.host but some reiteration phases (validation & correction loops in the adaptive pipeline) are still half-baked. The core pipeline works, but edge cases in the LLM correction loop may produce inconsistent results. Shipping anyway because perfect is the enemy of shipped.

## 🎉 What's New in v0.4.0

### 🎨 Redesigned User Interface
- **New Project Window Redesign**: Compact, space-efficient layout that follows Windows XP design language
  - Reduced window size from 800x750 to 550x650 pixels
  - Grouped sections with clear headers and icons
  - Scrollable content area with fixed header and footer
  - Blue gradient header matching the ModelSettings aesthetic

### 🌈 Full Theme Support
- **Three Beautiful Themes**:
  - **Bliss** (Windows XP-style): Clean white/gray/blue aesthetic
  - **Terminal** (Matrix-style): Green-on-black hacker vibes
  - **Default**: Adaptive light/dark mode using CSS variables
- **ModelSettings Theme Integration**: All UI components now respect theme selection
- **Consistent Design Language**: All windows and components follow unified theme patterns

### ✨ Enhanced User Experience
- **Improved Space Utilization**: Better use of screen real estate across all windows
- **Theme-Aware Components**: Buttons, inputs, tabs, and all UI elements adapt to selected theme
- **Better Visual Hierarchy**: Organized sections with clear borders and headers
- **Responsive Design**: Components scale better on different screen sizes

</div>

---

## 📋 Overview

**Devussy** — Circular Development Methodology & Toolkit

Build software faster with stateless, agent-agnostic development plans.

Devussy isn't just software — it's a methodology for organizing development work so that plans are:

- **🔄 Reusable** – One plan works across humans and LLMs
- **📦 Portable** – Export as plain markdown, no runtime state
- **🤖 Agent-agnostic** – Any coding agent can pick up where the last one stopped

**Core concept:** Generate an optimal `devplan.md` for your project **once**, then execute it in a loop of **Circular Development**, passing clean handoff artifacts between phases and agents.

---

## ❌ The Problem

Traditional workflows suffer from:

- **Context loss** – Each new phase or agent has to re-read or rediscover prior work
- **Friction in handoffs** – Every human or AI handoff means re-explaining the project
- **Brittle plans** – Prose docs are hard to update and hard for agents to execute consistently
- **No clear next steps** – Every handoff needs bespoke "ok, now please do X, Y, Z" instructions

---

## ✅ The Devussy Solution: Circular Development

Devussy generates an optimal development plan for your project, then you execute it using **Circular Development**:

1. **Generate Once** – create `devplan.md` and per-phase scaffolding using Devussy  
2. **Execute Phase by Phase** – follow the handoff prompt for each phase  
3. **Update as You Go** – each phase updates its own doc **and** `devplan.md`  
4. **Handoff Seamlessly** – pass the phase document + devplan + next handoff to the next agent  
5. **Repeat** – each phase follows its predecessor’s updated handoff prompt  

Your devplan is a **stateless artifact** — pure markdown with no runtime requirements or hidden state.

---

## 💡 Why This Matters

### 👤 For Solo Developers

- Generate a complete plan at the start of a project  
- Execute each phase systematically, one at a time  
- Come back months later: `devplan.md` still has the full picture  
- Hand off to Claude/GPT mid-project: all context lives in the artifacts

### 👥 For Teams

- Senior dev generates the devplan  
- Junior dev receives: phase doc + `devplan.md` + handoff prompt  
- Junior executes Phase 2 with complete context  
- No more "what were you thinking here?" meetings

### 🤖 For AI-Assisted Development

- One devplan works with **any** LLM (Claude, GPT-4/5, Mistral, custom agents, etc.)  
- Handoff between LLMs without rewriting prompts  
- Each phase adapts based on what the previous phase learned  
- Stateless handoff means **zero vendor lock-in**

---

## 🛠️ How It Works: Adaptive 7-Stage Pipeline

### Stage 1: Generation (Devussy Software)

Devussy turns your project idea into an optimal devplan using a **7-stage adaptive pipeline** that automatically scales complexity based on your project:

#### The 7-Stage Adaptive Pipeline

1. **Interview & Requirements** (`interview.json`)
   - Guided Q&A captures goals, constraints, target stack
   - Output: structured data with no LLM orchestration yet

2. **Complexity Analyzer** (`complexity_profile.json`)
   - Pure-Python scoring rubrics rate difficulty
   - Estimates phase count and selects template depth (minimal/standard/detailed)
   - Deterministic scoring drives all downstream branching

3. **Adaptive Design Generator** (`design_draft.md`)
   - LLM combines interview + complexity profile
   - Small projects stay tiny; big systems get richer multi-module designs
   - Complexity-aware branching prevents over-engineering

4. **Design Validation & Correction Loop** (`validated_design.md`)
   - Rule-based checks + LLM sanity reviewer
   - Catches inconsistencies, hallucinated services, scope creep, missing tests
   - Iterative correction loop stabilizes design before devplan generation

5. **Adaptive Devplan Generator** (`devplan.md + phases.json`)
   - Generates dynamic phase count based on validated design + complexity
   - Explicit tests and acceptance criteria for each milestone
   - Tiny plans for tiny projects, full roadmaps for complex builds

6. **Pipeline Execution & Checkpoints** (`artifacts + devplan.zip`)
   - Phases run with streaming output and checkpointing
   - Schema-validated artifacts ensure consistency
   - Recoverable at every checkpoint, ready for multiple LLM providers

7. **Frontend, Downloads & Circular Handoff** (`devplan.zip + handoff.md`)
   - Visualizes complexity, phases, and validation results
   - One-click export for agent handoffs
   - Final `handoff.md` instructs next agent how to continue work

**Quick Start - Interactive Interview (Recommended):**

```bash
# Clone + editable install
git clone https://github.com/mojomast/devussy.git
cd devussy
pip install -e .

# Run the interactive adaptive pipeline
python -m src.cli interactive
```

**What happens:**

1. **Interactive Interview** – You describe your project via console Q&A (type `/done` when finished)
2. **Adaptive Analysis** – Devussy scores project complexity and selects optimal depth (minimal/standard/detailed)
3. **Design Generation** – Creates architecture with validation and optional correction loops
4. **DevPlan Creation** – Generates phase-specific plans with adaptive depth
5. **Parallel Streaming** – Terminal UI shows ~5 phases being generated in real-time

**Outputs (files):**

- `devplan.md` – Complete project plan with anchored sections for circular development
- `phase*.md` – Per-phase detailed plans (e.g., `phase1.md`, `phase2.md`)
- `handoff.md` – **The single handoff file** that tells agents what to do next

**For advanced usage and visual project management, use the [Web UI](#web-ui-devussy-web) instead.**

### Stage 2: Execution (Circular Development)

You (or any agent) then execute each phase using the **circular handoff pattern**.

**How Circular Development Works:**

Each phase follows this loop:

1. **Read** `handoff.md` – Learn what part of which phase doc to focus on
2. **Execute** – Do the work described in that phase section
3. **Update Phase Doc** – Record discoveries, decisions, and blockers in the phase file (e.g., `phase1.md`)
4. **Update DevPlan** – Update anchored sections in `devplan.md` (constraints, risks, timeline)
5. **Update Handoff** – Modify `handoff.md` to point the next agent to the next slice of work
6. **Handoff** – Pass `handoff.md` + `devplan.md` + phase docs to next agent (or new context window)

**Example: Phase 1 → Phase 2 Handoff**

```
Phase 1 Agent:
  ├─ Reads: handoff.md ("Focus on Phase 1, sections 1.1-1.3")
  ├─ Does: Planning work, discovers "Need 3× more compute"
  ├─ Updates: phase1.md (adds discovery notes)
  ├─ Updates: devplan.md (updates <!-- PROGRESS_LOG_START --> section)
  └─ Updates: handoff.md ("Next agent: Focus on Phase 2, section 2.1")

Phase 2 Agent:
  ├─ Reads: handoff.md ("Focus on Phase 2, section 2.1")
  ├─ Reads: devplan.md (sees updated compute requirement)
  └─ Continues: Design work with new constraint
```

**Key Principle:** `handoff.md` is **always** the single source of truth for "what to do next" – it references which phase doc and which sections within that doc to work on.

### The Three Artifacts That Travel Together

Each handoff includes three artifacts:

| Artifact | What's In It | Why It Matters |
|----------|--------------|----------------|
| `handoff.md` | Current focus area, next steps, which phase/sections to work on | **Single source of truth** for "what to do next" |
| `devplan.md` | Full project context with anchored sections for updates | Single source of truth for project state |
| Phase Documents (`phase*.md`) | Phase-specific progress, decisions, blockers | Shows what's been done in each phase |

**Critical: Always use `handoff.md`** – Not `phase-1-handoff.md` or `phase-2-handoff.md`. There is only **one handoff file** that gets updated to point agents to the correct phase and section.

**Example Flow:**

```
Agent A:
  └─ Reads: handoff.md ("Work on Phase 1, tasks 1-3")
  └─ Discovers: "We need 3× more compute than planned"
  └─ Updates: phase1.md (adds discovery notes)
  └─ Updates: devplan.md (updates <!-- PROGRESS_LOG_START --> anchor)
  └─ Updates: handoff.md ("Next: Work on Phase 2, task 1 with 3× compute constraint")

Agent B receives:
  ├─ handoff.md ("Work on Phase 2, task 1 with 3× compute constraint")
  ├─ devplan.md (contains updated compute requirement in anchored section)
  └─ phase1.md (shows Phase 1 discoveries)
```

No "hidden" context. No re-explanations. No per-phase handoff files.

---

## Agent-Ready Artifacts (Drop-In Folder for Any Coding Agent)

Every pipeline run writes a deterministic set of files to `docs/` and/or `output_*` (e.g., `output_0/`):

- `devplan.md` – Top-level multi-phase plan with **anchored sections** (see `AGENTS.md`)
- `phase*.md` – Per-phase files (e.g., `phase1.md`, `phase2.md`)
- `handoff.md` – **The single handoff file** that tells agents what to focus on next
- Supporting config/checkpoint files (for resuming runs)

This layout is designed so you can treat the output like a portable project brief:

1. **Start Phase Slice** – Prompt any agent to read `handoff.md` and execute the specified tasks
2. **Agent Works** – Agent reads specified phase doc sections, does the work, updates anchored sections
3. **Agent Updates Handoff** – Agent updates `handoff.md` to point to next slice of work
4. **Switch Context** – In another coding agent (ChatGPT, Claude, Roo Code, Cursor, etc.), tell them to read `handoff.md` and continue
5. **Repeat** – Each agent follows `handoff.md` → updates phase docs → updates `devplan.md` → updates `handoff.md`

Because everything is plain markdown with **stable anchors** (see `AGENTS.md`), any agent can safely:

- Understand the current project state
- See which phases/tasks are done vs TODO
- Update anchored sections without breaking structure
- Keep the same folder committed in git as single source of truth

**For more details on anchor-based context management, see `AGENTS.md` in the repo root.**

---

## What's in this branch (adaptive-llm-clean)

This branch focuses on a cleaned-up, adaptive LLM pipeline plus the existing CLI / TUI engine and web UI:

### Core pipeline

- Multi-stage flow: Interview → Design → DevPlan → Detailed DevPlan (per-phase) → Handoff

Provider-agnostic LLM client layer (OpenAI, OpenAI-compatible, Requesty, Aether, AgentRouter, etc.)

Async, checkpointed execution with resumable runs

Adaptive complexity pipeline

Automatic complexity scoring and depth selection (minimal / standard / detailed)

Phase count estimation and depth-aware templates

Design validation with rule-based + LLM checks

Optional correction loop that iterates until the design is “good enough”

Interfaces

CLI for one-shot or scripted runs (python -m src.cli ...)

Interactive terminal UI (Textual) that streams multiple phases live

Next.js web UI in devussy-web/ with SSE streaming and basic analytics

Agent-friendly docs

Stable anchor comments in planning docs

AGENTS.md, START_HERE.md, DEVPLAN_FOR_NEXT_AGENT.md, HANDOFF_FOR_NEXT_AGENT.md to guide AI tooling

Requirements
Python 3.9+

Node.js 18+ (for the Next.js frontend)

An LLM API key (OpenAI, Aether, Requesty, AgentRouter, or other OpenAI-compatible provider) 
Install
Clone and install in editable mode:

```bash
git clone https://github.com/mojomast/devussy.git
cd devussy
pip install -e .
```

Sanity-check the CLI:

```bash
python -m src.cli version
```

---

## ⚙️ Configure API Keys

Devussy reads standard environment variables (or a `.env` file in the repo root):

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Generic OpenAI-compatible
GENERIC_API_KEY=...
GENERIC_BASE_URL=https://api.your-openai-compatible.com/v1

# Requesty
REQUESTY_API_KEY=...

# Aether AI
AETHER_API_KEY=...
```

You can also set per-stage keys (e.g., `DESIGN_API_KEY`, `DEVPLAN_API_KEY`) if you want different providers or models per phase.

**For visual configuration and advanced settings, use the [Web UI](#web-ui-devussy-web).**

---

## 💻 Command Line Usage

### Primary Command: Interactive Adaptive Pipeline

```bash
python -m src.cli interactive
```

This single command runs the complete adaptive pipeline with an interactive interview.

**What it does:**

1. Runs a console-based LLM interview about your project
2. Automatically scores project complexity (minimal/standard/detailed)
3. Generates validated design with optional correction loops
4. Creates depth-aware devplan with phase-specific plans
5. Streams all phases in parallel using the Textual terminal UI

**For all other features** (project management, visual editing, advanced configuration), use the [Web UI](#web-ui-devussy-web).

### Utility Commands

```bash
# Check version
python -m src.cli version

# List saved checkpoints
python -m src.cli list-checkpoints

# Cleanup old checkpoints (keep 5 most recent)
python -m src.cli cleanup-checkpoints --keep 5
```

**Note:** Non-interactive pipeline commands (`run-full-pipeline`, `run-adaptive-pipeline`) are available but not recommended for general use. The interactive mode provides the best user experience.

---

## Web UI (devussy-web/)

The bundled Next.js app gives you a visual, multi-window view of the pipeline with live streaming.

From the repo root:

```bash
# Terminal 1: Python streaming backend
python devussy-web/dev_server.py

# Terminal 2: Next.js frontend
cd devussy-web
npm install      # first run only
npm run dev
```

Then visit [http://localhost:3000](http://localhost:3000).

**Highlights:**

- Draggable windows for each phase (interview, design, devplan, handoff)
- Real-time streaming via Server-Sent Events (SSE)
- Per-phase model configuration with shared defaults
- Lightweight analytics stored locally in `analytics.db` with opt-out support

---

## Checkpoints

The pipeline saves checkpoints so you can pause and resume.

**Common commands:**

```bash
# List existing checkpoints
python -m src.cli list-checkpoints

# Delete a specific checkpoint
python -m src.cli delete-checkpoint <key>

# Cleanup old checkpoints, keeping the most recent N
python -m src.cli cleanup-checkpoints --keep 5
```

Checkpoint keys are printed as the pipeline runs (e.g., `myproj_pipeline`).

**For advanced streaming configuration, concurrency tuning, and detailed backend settings, use the [Web UI](#web-ui-devussy-web) or see `STREAMING_GUIDE.md`.**

---

## 📁 Key Files & Folders

**Agent Documentation (Start Here):**
- `AGENTS.md` – **Critical**: Anchor-based context management patterns
- `handoff.md` – The single handoff file that guides circular development
- `devplan.md` – Main project plan with anchored sections
- `phase*.md` – Per-phase detailed plans

**Code & Templates:**
- `src/` – Core pipeline, CLI, interview engine, LLM adapters
- `templates/` – Jinja templates for document generation
- `adaptive_llm_implementation/` – Adaptive complexity & validation logic

**Output:**
- `docs/`, `output_*/` – Generated project artifacts

**Web UI:**
- `devussy-web/` – Next.js frontend for visual project management

---

## Circular Development Philosophy

Software development isn't linear — it's circular:

- You plan, you discover constraints, you update the plan
- You build, you hit edge cases, you iterate
- You test, you find bugs, you refine

Devussy bakes that into the process:

- **Devplans are living documents** — Updated as each phase learns
- **Agents/teams collaborate on a single plan** — Stateless, no hidden state
- **Handoff prompts adapt** — Each phase's instructions include previous discoveries
- **Progress is always captured** — `devplan.md` remains your single source of truth

---

## When to Use Devussy

### ✅ Use Devussy if:

- You're starting a new project from scratch
- You want to hand off between humans and AI seamlessly
- Your projects naturally split into multiple phases of work
- You want a structured, reusable plan
- You're tired of re-explaining context to new team members/agents

### ❌ Probably not for you if:

- You're only doing a tiny one-off task
- You have a rigid, non-iterative waterfall process
- You don't need multi-phase handoffs or AI-assisted dev at all

---

## FAQ

**Q: How is Devussy different from other planning tools?**

Most planning tools create a plan and stop. Devussy generates an initial plan and gives you a methodology for executing it with stateless handoffs. You can hand off `devplan.md` + phase artifacts to any agent (human or AI) and they have full context.

**Q: Can I use Devussy with my favorite LLM?**

Yes. Devussy supports any LLM with an OpenAI-style API. Providers like OpenAI, Aether, Requesty, AgentRouter, and generic OpenAI-compatible endpoints are supported.

**Q: What makes a devplan "stateless"?**

A stateless devplan has no hidden state, no database, no runtime dependencies. It's pure markdown. You can read it on day 1 or day 365 and get the same context. You can hand it to any agent without setup.

**Q: What if I discover new constraints during Phase 2?**

Update the anchored sections in `devplan.md` (using the `<!-- PROGRESS_LOG_START -->` and `<!-- NEXT_TASK_GROUP_START -->` anchors), then update `handoff.md` to point the next agent to the relevant phase section with the new constraints. There's only one `handoff.md` file that gets continuously updated.

**Q: Can my team collaborate on one devplan?**

Yes. Devplans are markdown files, so you can:

- Put them in Git and use PRs
- Share them via Slack/Discord
- Edit collaboratively with conflict resolution

**Q: Does Devussy support existing codebases?**

Not yet! Stay tuned!

---

## Contributing

Issues, PRs, and vibes are welcome. See `DevDocs/` and `START_HERE.md` for internal dev notes and roadmap.

---

<p align="center">
  <em>We out here shippin' code and slammin' Cadillac doors. BRRRRRRRRRRRRRRRRRRRRRRRRRR</em>
  <br>
  Copyright 2025 Kyle Durepos (mojomasta@gmail.com)
</p>

