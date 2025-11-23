# Handoff for Next Agent – Devussy App Framework & Circular DevPlan

## 1. Status Overview

**Scope of this handoff**

- This handoff is specifically about the **Devussy Application Framework and Cross‑App Integration** described in `appdevplan.md`.
- The focus is to turn Devussy into a **modular “desktop in the browser”** with:
  - An `AppDefinition` + `AppRegistry`
  - A cross‑app event bus
  - Share links that deep‑link into pipeline state
  - Declarative container/nginx integration per app

**Current status**

- `appdevplan.md` has been cleaned up and is now a coherent design doc:
  - Stray `raw.githubusercontent.com` artifacts removed.
  - Headings normalized.
  - Code samples fenced and readable.
  - Intro updated to match the **current** IRC integration (no stale branch references).
- The **implementation** of the framework is **not done yet**:
  - `src/app/page.tsx` still uses a hard‑coded `WindowType` union and switch.
  - There is no `AppRegistry` or app module structure yet.
  - No event bus is wired into the app tree.
  - No `/share` route and no share‑link handling in `IrcClient.tsx`.
  - Docker + nginx are still maintained manually (no `generate-compose` script).

Think of `appdevplan.md` as the **design baseline**. Your job is to advance implementation while keeping the plan and handoff updated so any other agent can resume easily.

---

## 2. Circular, Stateless Development Principles

For this work, please follow these principles:

- **Single source of truth**  
  - Treat `appdevplan.md` as the canonical design for the app framework.
  - When you change direction, update `appdevplan.md` and this handoff, not just the code.

- **Small, labeled phases**  
  - Work in **small stages** (e.g. “App types”, “Registry wiring”, “Event bus MVP”, “Share link MVP”).
  - At the end of each stage:
    - Document what you did.
    - Document what’s left and any tradeoffs.
    - Keep it in Markdown so the next agent can pick up from text alone.

- **No hidden state**  
  - Assume the next agent will only have:
    - The repo
    - `appdevplan.md`
    - The latest handoff docs
  - Don’t rely on your own local context or mental notes—write everything important down.

- **Agent‑agnostic continuity**  
  - Write instructions in a way that any coding model (Devussy, GPT, Claude, Gemini, etc.) can follow:
    - Clear file paths, function names, and expected behaviors.
    - Explicit constraints (type signatures, props, env vars).
    - Short, precise tasks.

---

## 3. Key Reference Files

The next agent should read these before coding:

- `appdevplan.md`  
  – Design for the app framework, event bus, share links, compose generation.

- `devussy-web/src/app/page.tsx`  
  – Current window manager, `WindowType` union, IRC window integration.

- `devussy-web/src/components/addons/irc/IrcClient.tsx`  
  – IRC client behavior and how it currently connects to `/ws/irc/`.

- `devussy-web/docker-compose.yml` and `devussy-web/nginx/nginx.conf`  
  – Current services (`frontend`, `streaming-server`, `nginx`, `ircd`) and nginx proxy to `/ws/irc/`.

- `IRCPLAN.MD` and `devussy-web/irc/README.md`  
  – Background on how IRC was implemented.

---

## 4. What’s Completed vs. What’s Open

### Completed (for this track)

- `appdevplan.md`:
  - Restructured with Markdown headings and fenced TypeScript samples.
  - Context updated to match the working IRC integration.
  - Examples for:
    - `AppDefinition`, `DockerServiceDef`, `NginxProxyDef`, `AppContext`.
    - `AppRegistry` usage.
    - Event bus class and hook (`useEventBus`).
    - Share link format and helper.
    - Declarative service / proxy definitions per app.

No code has yet been refactored to follow that plan.

### Open Work (high level)

1. **Introduce the app framework types in the frontend codebase.**
2. **Refactor window management to use the registry instead of hard‑coded `WindowType`.**
3. **Implement a basic event bus and wire it into pipeline + IRC.**
4. **Add share‑link generation and consumption paths.**
5. **(Optional) Start the compose/nginx generation script.**

You should not attempt to finish everything in one go. Pick a clear sub‑phase, implement it cleanly, and update this handoff for the next agent.

---

## 5. Recommended Next Phase: App Types & Registry Skeleton

**Objective**

Create the foundational TypeScript types and registry structure, without yet refactoring `page.tsx` to use them.

**Suggested steps**

1. **Create a central app types file**
   - Location proposal: `devussy-web/src/apps/appTypes.ts` (or similar).
   - Implement the `AppDefinition`, `DockerServiceDef`, `NginxProxyDef`, and `AppContext` interfaces as shown in `appdevplan.md`.
   - For now, keep `AppContext.getState`/`setState` typed as `any` (as in the doc) to avoid blocking on global state design.

2. **Create a minimal `AppRegistry.ts`**
   - Location: `devussy-web/src/apps/AppRegistry.ts`.
   - Export a `Record<string, AppDefinition>`.
   - For the first pass, wire in just two entries:
     - A `PipelineApp` placeholder that maps to the existing pipeline flows.
     - An `IrcApp` placeholder that wraps `IrcClient`.

3. **Document what you did**
   - Add a short “Implementation Status” note in `appdevplan.md` under the App Interface section:
     - e.g., “App types and `AppRegistry` created; currently used only as scaffolding.”

4. **Update this handoff**
   - Add a small section summarizing:
     - Files created/modified.
     - How to add a new app entry.
     - Any design tradeoffs you made (e.g., where you mounted `apps/` in the src tree).

**What to avoid in this phase**

- Don’t change `WindowType` or `page.tsx` behavior yet.
- Don’t introduce the event bus or share links yet.
- Don’t change Docker/nginx here.

---

## 6. Later Phases (For Subsequent Agents)

These should be separate phases, each with its own mini-handoff:

1. **Window Manager Refactor**
   - Replace `WindowType` union with `keyof typeof AppRegistry`.
   - Implement `spawnAppWindow(appId, ...)` and `renderAppContent`.
   - Ensure:
     - Existing pipeline flow and auto-open IRC still behave identically.
     - Taskbar and Start Menu derive from `AppRegistry`.

2. **Event Bus Integration**
   - Implement the `EventBus` class and `EventBusContext` from `appdevplan.md`.
   - Wrap `page.tsx` (or a higher layout) with `<EventBusContext.Provider value={bus}>`.
   - Replace ad‑hoc callbacks (especially around “plan generated” or notifications) with events.
   - First cross‑app scenario:
     - Pipeline emit: `planGenerated`.
     - IRC listens and posts a message into `#devussy-chat`.

3. **Share Links**
   - Add `generateShareLink(stage, data)` helper.
   - Add “Share” buttons to design/plan/execute views.
   - Implement:
     - `/share?payload=...` route.
     - `IrcClient` link detection and `openShareLink` emission.
     - Top‑level handler that uses `handleLoadCheckpoint` and `spawnAppWindow`.

4. **Compose / Nginx Generation**
   - Implement `scripts/generate-compose.ts` as described.
   - Keep existing `docker-compose.yml` and `nginx.conf` as ground truth until the generator is validated.

Each of these phases should end with:

- Short summary in this handoff.
- Status update in `appdevplan.md` (`Status: proposed / implemented / partial`).
- Any new testing notes (manual steps, scripts, or test files).

---

## 7. How to Work as the Next Agent

When you start a new phase:

1. **Read**
   - Skim `appdevplan.md`.
   - Read `apphandoff.md` top-to-bottom.
   - Skim the files you’ll be editing.

2. **Define a small scope**
   - Write a short “Phase Objective” section in this handoff.
   - List 3–6 concrete tasks you will complete.

3. **Implement**
   - Make minimal, well-isolated changes.
   - Keep behavior stable as you refactor (especially in `page.tsx`).

4. **Verify**
   - At least:
     - Run the frontend and manually test:
       - Opening pipeline windows.
       - Auto-open IRC.
     - For event bus/share‑link phases, test the full flow you introduce.

5. **Update docs**
   - Update `appdevplan.md` with any architectural shifts.
   - Update this handoff:
     - Mark your phase as “COMPLETE” or “PARTIAL”.
     - Document remaining work, caveats, and follow‑ups.

---

## 8. Immediate Next Action

For the very next agent, the recommended first move is:

> Implement the foundational app types and `AppRegistry` skeleton as described in section 5, without changing runtime behavior.

Once that’s complete and documented, the following agent can safely pick up the **window manager refactor** or **event bus** phase, using just the codebase, `appdevplan.md`, and this evolving handoff.
