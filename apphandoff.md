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
- The **implementation** of the framework is **partially complete**:
  - App types, an `AppRegistry`, and initial app modules under `devussy-web/src/apps/` are in place and used by the window manager for `WindowType`, default sizes, Start menu categories, and IRC rendering.
  - `devussy-web/src/app/page.tsx` still uses a manual `renderAppContent` switch for the main pipeline windows, but now wraps the desktop/window manager in an `EventBusProvider` so apps can access a shared event bus.
  - The event bus powers several cross-app notifications: `planGenerated` (pipeline → IRC), `shareLinkGenerated` (pipeline share buttons → IRC announcements), `openShareLink` (IRC share links → top-level checkpoint restore), and `executionCompleted` (execution view → IRC).
  - Share links are fully wired end-to-end: pipeline views generate `/share?payload=...` URLs, `/share` validates and persists the payload to `sessionStorage`, IRC renders clickable “[Open shared Devussy state]” buttons for incoming share links, and the desktop restores state via `handleLoadCheckpoint` when handling `openShareLink` or a stored payload.
  - An initial `scripts/generate-compose.ts` exists and generates
    `devussy-web/docker-compose.apps.generated.yml` and
    `devussy-web/nginx/conf.d/apps.generated.conf` from any app-level
    `services` / `proxy` / `env` metadata. `IrcApp` now declares `services`,
    `proxy`, and `env` metadata for the IRC backend and WebSocket alias, and
    `nginx/nginx.conf` includes `/etc/nginx/conf.d/*.conf` so generated location
    blocks are picked up. The generated compose file defines additional
    app-provided services plus a `frontend` environment overlay and is still
    layered manually on top of `docker-compose.yml` rather than being wired into
    the default dev/prod commands.

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

- Code has begun to be refactored to follow that plan; see the Window Manager Refactor phase log below for details.

### Open Work (high level)

1. **Introduce the app framework types in the frontend codebase.** – **DONE**; see *Phase Log: App Types & Registry Skeleton* below.
2. **Refactor window management to use the registry instead of hard‑coded `WindowType`.** – **PARTIAL**; see *Phase Log: Window Manager Refactor*.
3. **Implement a basic event bus and wire it into pipeline + IRC.** – **PARTIAL (v1 in use)**; core notifications are now event-driven (`planGenerated`, `shareLinkGenerated`, `openShareLink`, `executionCompleted`), but there is still no generic `AppContext` state model and most callbacks remain direct props.
4. **Add share-link generation and consumption paths.** – **COMPLETE (v1)**; see *Phase Log: Share Links*.
5. **Start and extend the compose/nginx generation script.** – **PARTIAL**; a minimal generator exists, `IrcApp` now declares `services`/`env` metadata for the IRC backend and proxy metadata for an IRC WebSocket alias, and `nginx/nginx.conf` includes `/etc/nginx/conf.d/*.conf` to consume generated fragments. The generated compose file is not yet wired into the default dev/prod commands.

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

### Phase Log: App Types & Registry Skeleton (STATUS: COMPLETE)

- **Files created (frontend scaffolding only, no behavior changes):**
  - `devussy-web/src/apps/appTypes.ts`
  - `devussy-web/src/apps/pipeline.tsx`
  - `devussy-web/src/apps/irc.tsx`
  - `devussy-web/src/apps/AppRegistry.ts`
- **Current usage:**
  - `PipelineApp` is a placeholder component; the existing pipeline windows in `devussy-web/src/app/page.tsx` still control runtime behavior.
  - `IrcApp` wraps the existing `IrcClient` component so it can be referenced from the registry later.
  - `AppRegistry` is defined but not yet used by the window manager, event bus, or Docker/nginx tooling.

**How to add a new app entry (future phases):**

- Create `devussy-web/src/apps/<id>.tsx` exporting an `AppDefinition`.
- Import it into `devussy-web/src/apps/AppRegistry.ts` and add it to the `AppRegistry` map.

---

## 6. Later Phases (For Subsequent Agents)

These should be separate phases, each with its own mini-handoff:

1. **Window Manager Refactor**
   - Replace `WindowType` union with `keyof typeof AppRegistry`.
   - Implement `spawnAppWindow(appId, ...)` and `renderAppContent`.
   - Ensure:
     - Existing pipeline flow and auto-open IRC still behave identically.
     - Taskbar and Start Menu derive from `AppRegistry`.

### Phase Log: Window Manager Refactor (STATUS: PARTIAL)

- **Code changes (frontend):**
  - `devussy-web/src/app/page.tsx`:
    - `WindowType` is now defined as `keyof typeof AppRegistry`.
    - Window sizing now uses `AppRegistry[appId].defaultSize` via `getWindowSize`, preserving the old default sizes.
    - Introduced `spawnAppWindow(appId, ...)` as a thin wrapper around the existing `spawnWindow`, and updated all call sites to use it.
    - The existing `renderWindowContent` function was renamed to `renderAppContent`; most window types still use a manual `switch`, but the `'irc'`, `'help'`, and `'model-settings'` cases now render via `AppRegistry[appId].component` instead of importing their components directly.
    - `renderAppContent` now includes a generic `default` branch that renders any app whose `AppRegistry[appId]` entry provides a `component`, so new simple apps can be added via the registry without changing the switch, while the pipeline views still use dedicated branches in `page.tsx`.
  - `devussy-web/src/apps/AppRegistry.ts`:
    - Added placeholder `AppDefinition` entries for `init`, `interview`, `design`, `plan`, `execute`, and `handoff` with default sizes that match the current window manager behaviour.
    - Added concrete, registry-driven `AppDefinition` entries for `irc`, `help`, and `model-settings` implemented in `src/apps/irc.tsx`, `src/apps/help.tsx`, and `src/apps/modelSettings.tsx`.
  - `devussy-web/src/components/window/Taskbar.tsx`:
    - Now accepts an `onOpenApp(appId)` callback.
    - In the Bliss theme, the **Most Used** entries (New Project, Help & Support, IRC Chat) and the **All Programs** list launch apps via `onOpenApp`; the All Programs list is generated from `AppRegistry` using each app's `startMenuCategory`.
    - In the non-Bliss theme, the floating taskbar's New/Help/Chat buttons also call `onOpenApp(appId)` so that launches go through the same registry-driven path.

- **Behavioural status:**
  - Pipeline flow (Interview → Design → Plan → Execute → Handoff) and auto-open IRC behaviour remain identical to the previous implementation.
  - The registry is now the single source of truth for default window sizes and valid app IDs, powers the IRC/Help/Model Settings window rendering, and feeds the Bliss Start menu's All Programs list. A generic `renderAppContent` fallback renders registry-provided components for simple apps, but the main pipeline windows still use bespoke branches in the `renderAppContent` switch.

- **Remaining work for this phase:**
  - Optionally use the registry-driven pattern for future non-pipeline apps, while **leaving the main pipeline windows (`init`, `interview`, `design`, `plan`, `execute`, `handoff`) bespoke**. The pipeline UI flows are managed as a separate project and are intentionally not being wrapped behind `AppRegistry` in this track.
  - Once an `AppContext` / event bus exists, consider moving more window logic for add-on apps into their modules so the window manager becomes a thinner shell for non-pipeline functionality.

2. **Event Bus Integration**
   - Implement the `EventBus` class and `EventBusContext` from `appdevplan.md`.
   - Wrap `page.tsx` (or a higher layout) with `<EventBusContext.Provider value={bus}>`.
   - Replace ad‑hoc callbacks (especially around “plan generated” or notifications) with events.
   - First cross‑app scenario:
     - Pipeline emit: `planGenerated`.
     - IRC listens and posts a message into `#devussy-chat`.

### Phase Log: Event Bus Integration (STATUS: PARTIAL, v1 in use)

- **Code changes (frontend):**
- `devussy-web/src/apps/eventBus.tsx` defines an `EventBus` class, `EventBusProvider`, and `useEventBus` hook that provide a shared event bus instance to the web UI.
- `devussy-web/src/app/page.tsx` wraps the desktop/window manager in `EventBusProvider` (via an inner `PageInner` component) and:
  - Emits a `planGenerated` event from `handlePlanApproved` with `projectName`, `languages`, `requirements`, and the approved `plan`.
  - Subscribes to `openShareLink` from the bus and to a persisted `devussy_share_payload` in `sessionStorage` on first render, normalising both into a checkpoint-like object passed to `handleLoadCheckpoint` so shared state can be restored.
- `devussy-web/src/components/addons/irc/IrcClient.tsx` subscribes to:
  - `planGenerated` and appends a local `[Devussy]` notification message from `devussy-bot` into the default `#devussy-chat` channel whenever a new plan is approved.
  - `shareLinkGenerated` and either sends a PRIVMSG into `#devussy-chat` with a `[Devussy] Shared <stage> link: <url>` message (when connected) or logs a system message when IRC is disconnected.
  - `executionCompleted` and posts a `[Devussy] Execution phase completed for <project> (<n> phases)` message into `#devussy-chat` when the execution phase finishes.
  - These notifications are also mirrored into the `Status` tab as system
    messages, so cross-app events remain visible even when the IRC channel tab
    is not focused.

- **Behavioural status:**
- Core pipeline flow (Interview → Design → Plan → Execute → Handoff) and IRC connection behaviour remain unchanged; the event bus now drives the primary cross-app notifications for plan approval, share-link flow, and execution completion, while pipeline view props remain otherwise unchanged.

- **Remaining work for this phase:**
- Decide whether to introduce a richer `AppContext` abstraction on top of the event bus for registry-driven apps, and which additional callbacks (if any) should be migrated onto the bus.

3. **Share Links**
   - Add `generateShareLink(stage, data)` helper.
   - Add “Share” buttons to design/plan/execute views.
   - Implement:
     - `/share?payload=...` route.
     - `IrcClient` link detection and `openShareLink` emission.
     - Top‑level handler that uses `handleLoadCheckpoint` and `spawnAppWindow`.

### Phase Log: Share Links (STATUS: COMPLETE – v1)

- **Code changes (frontend):**
- `devussy-web/src/shareLinks.ts` defines a `ShareLinkPayload` shape and helper functions `generateShareLink(stage, data)` and `decodeSharePayload(encoded)` that JSON‑encode the payload and convert it to/from base64‑URL‑safe strings. `generateShareLink` returns `/share?payload=...` on the server and `"{origin}/share?payload=..."` in the browser.
- `devussy-web/src/app/share/page.tsx` implements the `/share` route. It:
  - Reads the `payload` query parameter via `useSearchParams`.
  - Uses `decodeSharePayload` to validate/parse the payload.
  - Shows a small summary of what is being shared (stage + optional project name).
  - Persists the raw encoded payload into `sessionStorage` under `devussy_share_payload`.
  - Offers an “Open Devussy” button that navigates back to `/`, with copy updated to reflect that the main desktop now *does* restore the shared state and open the appropriate window.
- `devussy-web/src/components/addons/irc/IrcClient.tsx`:
  - Scans message text for `/share?payload=` URLs using a `parseShareLinkFromText` helper that extracts the `payload` query parameter from either an absolute URL or a relative `/share?...` path.
  - Renders such links as a small `[Open shared Devussy state]` button instead of raw text.
  - On click, decodes the payload with `decodeSharePayload` and emits an `openShareLink` event on the global event bus with the `{ stage, data }` object.
  - Additionally subscribes to a `shareLinkGenerated` event (emitted by the pipeline share buttons) and posts a `[Devussy] Shared <stage> link: <url>` message into `#devussy-chat` whenever a new share URL is created.
- `devussy-web/src/app/page.tsx` (PageInner):
  - Subscribes to the `openShareLink` event via `useEventBus`. When fired, it treats `payload.data` as a checkpoint‑like object (`{ projectName, languages, requirements, design, plan, stage }`) and forwards it to `handleLoadCheckpoint`, which already knows how to restore project state and spawn the appropriate pipeline window.
  - On first render, checks `sessionStorage` for a saved `devussy_share_payload`, decodes it with `decodeSharePayload`, and again calls `handleLoadCheckpoint` so that opening `/share?...` in a new tab followed by “Open Devussy” correctly restores the shared state.
- `devussy-web/src/components/pipeline/DesignView.tsx`, `PlanView.tsx`, and `ExecutionView.tsx` each expose a “Share” button in the header. These buttons:
  - Build a stage‑appropriate data object (e.g. `{ projectName, requirements, languages, design }` for design; `{ design, plan, projectName }` for plan; `{ projectName, plan }` for execute).
  - Call `generateShareLink('design' | 'plan' | 'execute', data)` to produce a shareable URL.
  - Emit a `shareLinkGenerated` event on the global event bus with `{ stage, data, url }` so other apps (like IRC) can react.
  - Try to copy the URL to the clipboard and always fall back to showing it in a `window.prompt` so the user can paste it into IRC or elsewhere.

- **Behavioural status:**
- A user can now generate share links from the Design, Plan, and Execution views, paste them into IRC, and have other users click those links to restore the project state and open the corresponding pipeline window in their own Devussy session.
- Links opened directly (e.g. from email or another browser tab) hit `/share`, which validates and stores the payload, then "Open Devussy" returns to the main desktop where the share payload is consumed and applied via `handleLoadCheckpoint`.

- **Manual test script (current v1):**
- With the frontend + IRC running, create a sample project and:
  - From Design view, click **Share**, copy the URL, paste it into `#devussy-chat`, then in another session click `[Open shared Devussy state]` and verify that `/share` shows the correct stage/project and that “Open Devussy” restores the Design window with the expected project data.
  - Repeat from Plan and Execution views, confirming that the right window opens with plan / execution context restored.
  - Observe that when you click Share, IRC also receives a `[Devussy] Shared <stage> link: <url>` bot message via the `shareLinkGenerated` event.

- **Remaining work / follow‑ups:**
- Decide how much state should be included in share payloads vs. relying on backend checkpoints (e.g. minimal vs. full snapshots) and document that convention more explicitly if needed.
- Add automated tests (or at least keep this manual script up to date) that cover the end‑to‑end share flow for design, plan, and execution stages.

4. **Compose / Nginx Generation**
   - Implement and extend `scripts/generate-compose.ts` as described, gradually moving app-specific services (like IRC) into `AppDefinition.services` / `proxy` metadata.
   - Keep existing `docker-compose.yml` and `nginx.conf` as ground truth until the generator is validated.

### Phase Log: Compose / Nginx Generation (STATUS: COMPLETE)

- **Code changes (infra metadata):**
  - `devussy-web/src/apps/irc.tsx` defines `IrcApp.services` metadata that
    mirrors the existing `ircd` service in `devussy-web/docker-compose.yml`,
    `IrcApp.proxy` metadata for an IRC WebSocket alias path at `/apps/irc/ws/`
    pointing to an IRC backend on port 8080, and `IrcApp.env` metadata for the
    canonical frontend IRC env (`NEXT_PUBLIC_IRC_WS_URL`, `NEXT_PUBLIC_IRC_CHANNEL`).
  - `devussy-web/nginx/nginx.conf` includes `/etc/nginx/conf.d/*.conf` inside
    the TLS server block so that the generated
    `devussy-web/nginx/conf.d/apps.generated.conf` fragment is loaded
    automatically by nginx.
  - `scripts/generate-compose.ts` was moved to `devussy-web/scripts/generate-compose.ts` and updated to resolve imports correctly.
  - `devussy-web/package.json` now includes a `generate:compose` script that uses `ts-node` and `tsconfig-paths` to generate the config files.
  - `devussy-web/tsconfig.json` was updated with `"baseUrl": "."` to support `tsconfig-paths`.
- **Behavioural status:**
  - The existing `/ws/irc/` gateway path and `ircd` service in
    `docker-compose.yml` remain the ground truth and continue to power the
    Devussy IRC client. The new `/apps/irc/ws/` alias becomes available once
    `npm run generate:compose` has been run and nginx reloaded with the
    generated fragment.
- **Remaining work for this phase:**
  - Decide how and when to point `NEXT_PUBLIC_IRC_WS_URL` at the generated
    alias (versus the existing `/ws/irc/` path).

Each of these phases should end with:

- Short summary in this handoff.
- Status update in `appdevplan.md` (`Status: proposed / implemented / partial`).
- Any new testing notes (manual steps, scripts, or test files).

### Doc alignment: `appdevplan.md`

- In `appdevplan.md`, under **"Implementation status – Compose / Nginx generation (partial):"**, the third bullet is now out of date (it still says no apps declare `services` or `env` metadata). Replace that third bullet with:
  `- devussy-web/src/apps/irc.tsx now also declares IrcApp.services metadata that mirrors the existing ircd service and IrcApp.env metadata for the canonical frontend IRC env (NEXT_PUBLIC_IRC_WS_URL, NEXT_PUBLIC_IRC_CHANNEL), and scripts/generate-compose.ts collects services, proxy, and env from AppRegistry, emitting additional app‑provided services plus a frontend service environment overlay into devussy-web/docker-compose.apps.generated.yml alongside the nginx fragment. The script is still not wired into npm scripts (there is no generate:compose entry); developers are expected to run it manually and layer the generated compose file on top of docker-compose.yml.`

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
     - For event bus/share-link phases, test the full flow you introduce.

5. **Update docs**
   - Update `appdevplan.md` with any architectural shifts.
   - Update this handoff:
     - Mark your phase as “COMPLETE” or “PARTIAL”.
     - Document remaining work, caveats, and follow‑ups.

---

## 8. Immediate Next Action

For the very next agent on this track, the recommended first move is to
**validate and document the IRC compose/nginx overlay workflow**, keeping the
core pipeline windows as-is:

> Refine the deployment docs and run scripts so `scripts/generate-compose.ts`
> and the generated `docker-compose.apps.generated.yml` /
> `nginx/conf.d/apps.generated.conf` are routinely layered on top of
> `docker-compose.yml` / `nginx/nginx.conf` in a non-destructive way (for
> example via
> `docker compose -f docker-compose.yml -f docker-compose.apps.generated.yml up`).
> Decide whether `NEXT_PUBLIC_IRC_WS_URL` should continue pointing at `/ws/irc/`
> or switch to the generated `/apps/irc/ws/` alias, and update the env defaults
> accordingly. Do not remove or rewrite the handwritten docker/nginx files
> until the generator is validated; treat the generated artifacts as an
> overlay.

Once that’s complete and documented, a following agent can further expand
event bus usage or add new registry-driven apps that declare their own
services, using just the codebase, `appdevplan.md`, and this evolving
handoff.
