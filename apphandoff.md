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

### Phase Log: Window Manager Refactor (STATUS: COMPLETE – v2)

- **Code changes (frontend):**
  - `devussy-web/src/apps/appTypes.ts`:
    - Added `singleInstance?: boolean` to `AppDefinition` interface to support apps that should only have one window open at a time.
  - `devussy-web/src/app/page.tsx`:
    - `WindowType` is now defined as `keyof typeof AppRegistry`.
    - Window sizing now uses `AppRegistry[appId].defaultSize` via `getWindowSize`, preserving the old default sizes.
    - Introduced `spawnAppWindow(appId, ...)` as a thin wrapper around the existing `spawnWindow`, and updated all call sites to use it.
    - **v2**: `spawnAppWindow` now implements `singleInstance` logic: if an app has `singleInstance: true` and a window is already open, it focuses and restores the existing window instead of creating a duplicate.
    - The existing `renderWindowContent` function was renamed to `renderAppContent`; most window types still use a manual `switch`, but the `'irc'`, `'help'`, and `'model-settings'` cases now render via `AppRegistry[appId].component` instead of importing their components directly.
    - `renderAppContent` now includes a generic `default` branch that renders any app whose `AppRegistry[appId]` entry provides a `component`, so new simple apps can be added via the registry without changing the switch, while the pipeline views still use dedicated branches in `page.tsx`.
    - **v2**: Simplified `onOpenApp` handler to use `AppRegistry` generically for all apps except `init` and `interview` (which require special state setup). Removed redundant handlers `handleHelp`, `handleOpenIrc`, and `handleOpenModelSettings`.
  - `devussy-web/src/apps/AppRegistry.ts`:
    - Added placeholder `AppDefinition` entries for `init`, `interview`, `design`, `plan`, `execute`, and `handoff` with default sizes that match the current window manager behaviour.
    - Added concrete, registry-driven `AppDefinition` entries for `irc`, `help`, and `model-settings` implemented in `src/apps/irc.tsx`, `src/apps/help.tsx`, and `src/apps/modelSettings.tsx`.
  - `devussy-web/src/apps/help.tsx`, `src/apps/irc.tsx`, `src/apps/modelSettings.tsx`:
    - **v2**: Set `singleInstance: true` to prevent duplicate windows.
  - `devussy-web/src/components/window/Taskbar.tsx`:
    - Now accepts an `onOpenApp(appId)` callback.
    - In the Bliss theme, the **Most Used** entries (New Project, Help & Support, IRC Chat) and the **All Programs** list launch apps via `onOpenApp`; the All Programs list is generated from `AppRegistry` using each app's `startMenuCategory`.
    - In the non-Bliss theme, the floating taskbar's New/Help/Chat buttons also call `onOpenApp(appId)` so that launches go through the same registry-driven path.
    - **v2**: Removed `onHelp`, `onOpenIrc`, and `onOpenModelSettings` props as they are now handled by the generic `onOpenApp`.

- **Behavioural status:**
  - Pipeline flow (Interview → Design → Plan → Execute → Handoff) and auto-open IRC behaviour remain identical to the previous implementation.
  - The registry is now the single source of truth for default window sizes and valid app IDs, powers the IRC/Help/Model Settings window rendering, and feeds the Bliss Start menu's All Programs list.
  - `renderAppContent` now uses a generic fallback for `help`, `irc`, and any other registry app, passing `onClose` and `window.props`. `HelpApp` was refactored to be self-contained (managing its own state for "don't show again" and analytics opt-out).
  - The main pipeline windows (`init`, `interview`, `design`, `plan`, `execute`, `handoff`) still use bespoke branches in `page.tsx` as intended.
  - **v2**: Help, IRC, and Model Settings windows now enforce single-instance behavior. Clicking to open them again focuses the existing window instead of spawning duplicates.

- **Remaining work for this phase:**
  - None for the core refactor. Future work can focus on moving pipeline apps to the registry pattern if desired, but they are currently out of scope.


2. **Event Bus Integration**
   - Implement the `EventBus` class and `EventBusContext` from `appdevplan.md`.
   - Wrap `page.tsx` (or a higher layout) with `<EventBusContext.Provider value={bus}>`.
   - Replace ad‑hoc callbacks (especially around “plan generated” or notifications) with events.
   - First cross‑app scenario:
     - Pipeline emit: `planGenerated`.
     - IRC listens and posts a message into `#devussy-chat`.

### Phase Log: Event Bus Integration (STATUS: COMPLETE – v2)

- **Code changes (frontend):**
- `devussy-web/src/apps/eventBus.tsx` defines an `EventBus` class, `EventBusProvider`, and `useEventBus` hook that provide a shared event bus instance to the web UI.
- `devussy-web/src/app/page.tsx` wraps the desktop/window manager in `EventBusProvider` (via an inner `PageInner` component) and:
  - Emits a `planGenerated` event from `handlePlanApproved` with `projectName`, `languages`, `requirements`, and the approved `plan`.
  - Emits an `interviewCompleted` event from `handleInterviewComplete` with `projectName`, `requirements`, and `languages`.
  - Emits a `designCompleted` event from `handleDesignComplete` with `projectName` and `design`.
  - Subscribes to `openShareLink` from the bus and to a persisted `devussy_share_payload` in `sessionStorage` on first render, normalising both into a checkpoint-like object passed to `handleLoadCheckpoint` so shared state can be restored.
- `devussy-web/src/components/addons/irc/IrcClient.tsx` subscribes to:
  - `planGenerated` and appends a local `[Devussy]` notification message from `devussy-bot` into the default `#devussy-chat` channel whenever a new plan is approved.
  - `interviewCompleted` and posts a `[Devussy] Interview completed for project "<name>"` message.
  - `designCompleted` and posts a `[Devussy] System design completed for project "<name>"` message.
  - `shareLinkGenerated` and either sends a PRIVMSG into `#devussy-chat` with a `[Devussy] Shared <stage> link: <url>` message (when connected) or logs a system message when IRC is disconnected.
  - `executionCompleted` and posts a `[Devussy] Execution phase completed for <project> (<n> phases)` message into `#devussy-chat` when the execution phase finishes.
  - These notifications are also mirrored into the `Status` tab as system
    messages, so cross-app events remain visible even when the IRC channel tab
    is not focused.

- **Behavioural status:**
- Core pipeline flow (Interview → Design → Plan → Execute → Handoff) and IRC connection behaviour remain unchanged; the event bus now drives the primary cross-app notifications for interview completion, design completion, plan approval, share-link flow, and execution completion, while pipeline view props remain otherwise unchanged.

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

### Phase Log: Share Links Hardening (STATUS: COMPLETE – v2)

- **Code changes (frontend safety/typing):**
- `devussy-web/src/app/page.tsx`:
  - Hardened the `openShareLink` event handler and the `devussy_share_payload` sessionStorage restore path. Both paths now:
    - Validate that the decoded payload is an object.
    - Derive `stage` from `payload.stage` (or `payload.data.stage` as a fallback) and require it to be a non-empty string.
    - Treat the `data` field as optional and only spread it into the checkpoint object when it is a plain object.
    - Log and no-op if the payload is malformed or missing a valid `stage`, instead of risking odd pipeline state.
- `devussy-web/src/apps/eventBus.tsx`:
  - Introduced a lightweight `EventPayloads` map and `EventKey` type so known events have explicit payload shapes: `planGenerated`, `interviewCompleted`, `designCompleted`, `shareLinkGenerated`, `executionCompleted`, and `openShareLink` (typed as `ShareLinkPayload`).
  - Parameterised `EventBus.emit` and `EventBus.subscribe` over these keys to catch obvious type mismatches at compile time while retaining a string-indexed fallback (`[event: string]: any`) for future ad-hoc events.

- **Manual test script (updated):**
- With the frontend + IRC running, re-run the existing v1 script with an extra sanity check around bad payloads:
  - From Design, Plan, and Execution views, use **Share** to generate links, paste them into `#devussy-chat`, and in another session click `[Open shared Devussy state]` to verify:
    - `/share` shows the correct stage/project summary and persists `devussy_share_payload`.
    - Returning to `/` restores the right pipeline window and project state via `handleLoadCheckpoint`.
    - IRC receives a `[Devussy] Shared <stage> link: <url>` bot message in-channel and a mirrored system message in the Status tab.
  - As a negative check, manually craft or paste an obviously broken link, e.g. `/share?payload=not-base64` or a base64 payload missing a `stage` field, and confirm that:
    - `/share` reports the link as invalid when `decodeSharePayload` fails.
    - If a malformed payload ever reaches the desktop (e.g. via a future integration), `page.tsx` logs an error (`Ignoring ... invalid decode result` or `missing stage`) and **does not** call `handleLoadCheckpoint`.

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
  - `scripts/generate-compose.ts` was moved to `devussy-web/scripts/generate-compose.ts` and updated to resolve imports correctly; developers currently run it manually (for example via `npx ts-node scripts/generate-compose.ts`) when they need app-provided services and proxies.
  - `devussy-web/tsconfig.json` uses `"baseUrl": "."` together with standard path mappings so imports in the app and scripts resolve cleanly.
- **Behavioural status:**
  - The existing `/ws/irc/` gateway path and `ircd` service in
    `docker-compose.yml` remain the ground truth and continue to power the
    Devussy IRC client. The generated `/apps/irc/ws/` alias becomes available
    once the compose generator has been run and nginx reloaded with the
    generated fragment, but the canonical client WebSocket URL remains
    `/ws/irc/` for now.
- **Notes for this phase:**
  - `NEXT_PUBLIC_IRC_WS_URL` defaults to `/ws/irc/`.
  - The generator script (`npm run generate:compose`) has been updated to use `tsconfig-paths` to correctly resolve aliases during execution.
  - Verification confirmed that the script generates the expected artifacts and that `docker compose -f ...` layers them correctly.

### Phase Log: IRC compose/nginx overlay workflow (STATUS: COMPLETE)

- **Docs aligned:** `devussy-web/README.md` and `devussy-web/irc/README.md` now document the overlay workflow.
- **Script fixed:** `devussy-web/package.json` now includes `tsconfig-paths` and the `generate:compose` script uses it to resolve path aliases, fixing previous execution errors.
- **Verification:** Validated that `npm run generate:compose` produces `docker-compose.apps.generated.yml` and `nginx/conf.d/apps.generated.conf`.

Each of these phases should end with:

- Short summary in this handoff.
- Status update in `appdevplan.md` (`Status: proposed / implemented / partial`).
- Any new testing notes (manual steps, scripts, or test files).

### Doc alignment: `appdevplan.md`

- In `appdevplan.md`, the **"Implementation status – Compose / Nginx generation (partial)"** subsection now documents the IrcApp services/env metadata and the non-destructive `scripts/generate-compose.ts` overlay workflow. If you change how the generator or IRC infrastructure works, update that subsection accordingly so it remains the single source of truth for this phase.

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
**expand Event Bus usage** or **continue the Window Manager refactor**:

> **Option A (Event Bus):** Review `appdevplan.md` Section 5. Identify ad-hoc callbacks in `page.tsx` (e.g. notifications) and replace them with `useEventBus` events.
>
> **Option B (Window Manager):** Review `appdevplan.md` Section 6 (Later Phases). Continue refactoring `page.tsx` to use the registry for more apps, or clean up the `renderAppContent` logic.

Pick one, define a small scope, and update this handoff.



### Phase Log: Event Bus Expansion – executionStarted (STATUS: COMPLETE)

- **Code changes (frontend):**
  - `devussy-web/src/apps/eventBus.tsx`:
    - Added a typed `executionStarted` event to the `EventPayloads` map with `{ projectName?: string; totalPhases?: number }` so execution lifecycle can be observed by other apps.
  - `devussy-web/src/components/pipeline/ExecutionView.tsx`:
    - Emits `executionStarted` from `startExecution()` with the current `projectName` and `phases.length` before kicking off phase execution, mirroring the existing `executionCompleted` event.
  - `devussy-web/src/components/addons/irc/IrcClient.tsx`:
    - Subscribes to `executionStarted` via `useEventBus` and mirrors it into the **Status** tab as a system message of the form `[Devussy] Execution started for <project> (<N> phases).`, consistent with other cross-app notifications.

- **Behavioural status:**
  - No changes to core pipeline flow or existing IRC behaviour. The only visible change is an additional system-level status line when execution begins.

- **Remaining work / follow-ups:**
  - Optionally extend execution telemetry (e.g. per-phase progress events) via the event bus in a future phase if finer-grained updates are desired.


### Phase Log: Window Manager Refinement – AppRegistry-driven IRC title (STATUS: COMPLETE)

- **Code changes (frontend):**
  - `devussy-web/src/app/page.tsx`:
    - Updated the Bliss desktop "mIRC" icon double-click handler to derive the window title from `AppRegistry['irc'].name`, falling back to `"IRC Chat  #devussy-chat"` if needed. This keeps behaviour identical while making the IRC window title consistent with the central app registry.

- **Behavioural status:**
  - Double-clicking the desktop IRC icon still opens the IRC chat window as before; the title now tracks the `IrcApp` definition in `AppRegistry` so future renames do not require changes in `page.tsx`.

- **Remaining work / follow-ups:**
  - Future window-manager phases can continue moving non-pipeline apps toward fully registry-driven rendering and props, but those are out of scope for this small refinement.

### Phase Log: AppContext wrapper on EventBus (STATUS: COMPLETE – v1)

- **Code changes (frontend):**
  - `devussy-web/src/apps/eventBus.tsx`:
    - Added a `createAppContext(bus)` helper that wraps the existing typed `EventBus` in an `AppContext` implementation exposing `emit`, `subscribe`, `getState`, and `setState`. For now, `getState`/`setState` are no-ops, keeping this as a minimal adapter on top of the bus.
  - `devussy-web/src/app/page.tsx`:
    - Derives a shared `appContext` instance via `createAppContext(bus)` inside `PageInner` and passes it into registry-driven apps as an `appContext` prop.
    - The `model-settings` branch now calls the registry component with `appContext={appContext}` in addition to the existing `configs`, `onConfigsChange`, and `activeStage` props.
    - The generic registry branch that renders `help`, `irc`, and other simple apps now passes `appContext={appContext}` alongside `onClose` and any window props.
  - `devussy-web/src/components/addons/irc/IrcClient.tsx`:
    - Updated `IrcClient` to accept an optional `appContext?: AppContext` prop.
    - Internally, it now prefers the provided `appContext` for `subscribe`/`emit` operations and falls back to a small adapter over `useEventBus()` when no context is supplied, so existing behaviour remains unchanged.

- **Behavioural status:**
  - No visible changes to the desktop, pipeline, or IRC behaviour. Cross-app events (`planGenerated`, `interviewCompleted`, `designCompleted`, `shareLinkGenerated`, `executionStarted`, `executionCompleted`, `openShareLink`) continue to flow exactly as before.
  - Registry apps now have access to a unified `AppContext` wrapper on top of the global `EventBus`, which can be extended in later phases to include per-app or shared state without touching the window manager again.

- **Remaining work / follow-ups:**
  - Decide whether to introduce real `getState`/`setState` semantics (e.g. per-app state or shared global state) on top of the current no-op implementation.
  - Gradually migrate other registry apps (e.g. Help, Model Settings) to lean on `AppContext` rather than importing `useEventBus` directly if they gain cross-app interactions in the future.

### Phase Log: Python Testing Suite for App Framework & IRC Integration (STATUS: COMPLETE – v1)

- **Scope covered:**
  - **Share links flow**: encode/decode helpers and `/share` wiring.
  - **EventBus / AppContext notifications**: lifecycle events emitted from the pipeline and consumed by `IrcClient` + Status tab.
  - **Compose/nginx generator**: `scripts/generate-compose.ts` and its generated artifacts.
  - **Window manager & AppRegistry invariants**: registry-driven app IDs, `WindowType`, and `singleInstance` semantics.

- **Test modules implemented (integration level):**
  - `tests/integration/test_share_links_flow.py`
    - Uses a small TypeScript harness (`devussy-web/scripts/src/shareLinks_harness.ts`) via `npx ts-node` to round-trip payloads through `generateShareLink`/`decodeSharePayload`.
    - Asserts that valid payloads preserve `stage`/`projectName` and that malformed or `stage`-less payloads decode to `null` instead of throwing.
    - Statically verifies that the `/share` page uses `decodeSharePayload` and persists `devussy_share_payload` into `sessionStorage` before offering an "Open Devussy" button.
  - `tests/integration/test_event_bus_notifications.py`
    - Parses `devussy-web/src/apps/eventBus.tsx` to extract typed event keys and asserts that each has at least one emit or subscribe site in `page.tsx`, `ExecutionView.tsx`, or `IrcClient.tsx`.
    - Confirms that `IrcClient` subscribes to `planGenerated`, `interviewCompleted`, `designCompleted`, `shareLinkGenerated`, `executionStarted`, and `executionCompleted`, and that pipeline/ExecutionView emit the corresponding events.
  - `tests/integration/test_compose_generator.py`
    - Runs the real `npm run generate:compose` workflow under `devussy-web/`.
    - Asserts that `docker-compose.apps.generated.yml` and `nginx/conf.d/apps.generated.conf` are created.
    - Verifies that the compose overlay contains the `irc_ircd` service with the expected InspIRCd image, ports, and volumes, plus a `frontend` env block with `NEXT_PUBLIC_IRC_WS_URL` and `NEXT_PUBLIC_IRC_CHANNEL`.
    - Verifies that the nginx fragment defines a `/apps/irc/ws/` location proxying to `ircd:8080` with websocket headers.
  - `tests/integration/test_window_manager_registry.py`
    - Asserts that `WindowType` in `page.tsx` is defined as `keyof typeof AppRegistry`.
    - Checks that `AppRegistry.ts` includes the expected core app IDs (`init`, `interview`, `design`, `plan`, `execute`, `handoff`, `help`, `model-settings`, `pipeline`, `irc`).
    - Verifies that Help, IRC, and Model Settings apps are marked `singleInstance: true` in their app files.
    - Confirms that `Taskbar` in `page.tsx` is driven by a generic `onOpenApp` handler which calls `spawnAppWindow(appId as WindowType, appDef.name)` instead of bespoke handlers.

- **How to run the suite:**
  - From the repo root (with dev dependencies installed):
    - `pytest tests/integration/test_share_links_flow.py -v`
    - `pytest tests/integration/test_event_bus_notifications.py -v`
    - `pytest tests/integration/test_compose_generator.py -v`
    - `pytest tests/integration/test_window_manager_registry.py -v`
  - Or run all integration tests:
    - `pytest tests/integration -v`

- **Notes / follow-ups for future agents:**
  - The current suite is intentionally lightweight and biased toward structural/contract checks rather than spinning up a full Next.js dev server.
  - If you later introduce richer `AppContext` state, additional apps, or new event types, extend these tests (or add new ones in `tests/integration/`) to cover the new behaviour instead of relying solely on manual testing.
  - If browser-level end-to-end tests become desirable, they should be added as a separate phase (for example using Playwright or a similar tool) so this Python-based suite remains fast and easy to run on the remote host.

### Phase Log: AppContext State, Scratchpad App, and Execution Telemetry (STATUS: COMPLETE – v1)

- **Code changes (frontend behaviour):**
  - `devussy-web/src/apps/eventBus.tsx`:
    - `createAppContext(bus)` now maintains a shared in-memory `currentState` object and provides real `getState`/`setState` semantics instead of no-ops.
    - `setState(patch)` accepts either a partial object (merged into the existing state), a functional updater `(prev) => next`, or any other value (which replaces the state).
    - `EventPayloads` now includes a typed `executionPhaseUpdated` event with `{ projectName?, phaseNumber, phaseTitle?, status, totalPhases? }`.
  - `devussy-web/src/components/pipeline/ExecutionView.tsx`:
    - Emits `executionPhaseUpdated` whenever a phase transitions to **running**, **complete** (both explicit `done` and implicit end-of-stream), or **failed**.
    - Each event includes the project name, phase number/title, current status, and the total number of phases so listeners can produce concise telemetry.
  - `devussy-web/src/components/addons/irc/IrcClient.tsx`:
    - Subscribes to `executionPhaseUpdated` and mirrors per-phase execution telemetry into the **Status** tab as system messages of the form:
      - `[Devussy] Execution started for phase N (Title) of M in <project>.`
      - `[Devussy] Execution completed for phase N (Title) of M in <project>.`
      - `[Devussy] Execution failed for phase N (Title) of M in <project>.`
    - Keeps the existing `executionStarted` and `executionCompleted` summary messages unchanged.
  - `devussy-web/src/apps/scratchpad.tsx` and `src/apps/AppRegistry.ts`:
    - Introduced a new `ScratchpadApp` (`id: "scratchpad"`, `singleInstance: true`) registered in `AppRegistry` under the **Devussy** start menu category.
    - The `ScratchpadView` component:
      - Loads its initial contents from `appContext.getState().scratchpad` (when available) and falls back to `localStorage['devussy_scratchpad']`.
      - On change, updates both `localStorage` and `appContext` via `setState(prev => ({ ...prev, scratchpad: value }))` so other windows can observe or reuse the shared note text.
      - Provides a small **Clear** button that clears both local storage and the `scratchpad` key from shared `AppContext` state.

- **Behavioural status:**
  - The desktop, pipeline, and IRC chat flows behave as before, but you now have:
    - A **Scratchpad** window available from the Start menu / All Programs list that persists notes per browser and exposes them via `AppContext`.
    - Finer-grained execution telemetry in the **Status** tab, showing when individual phases start, complete, or fail, in addition to the existing high-level execution started/completed messages.
  - `AppContext` is still a lightweight abstraction over the global `EventBus` but now carries a real shared state object that registry-driven apps can use for simple cross-window coordination.

- **Remaining work / follow-ups:**
  - Decide whether to introduce per-app or namespaced slices of `AppContext` state (rather than a single shared bag) if more complex apps are added.
  - Extend `tests/integration/test_event_bus_notifications.py` or related tests if you want explicit assertions around the new `executionPhaseUpdated` event in addition to the existing generic checks.
  - Consider adding a small integration test or harness that exercises the Scratchpad app’s interaction with `AppContext` once more apps start consuming `scratchpad` content.
