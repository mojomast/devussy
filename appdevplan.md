DevPlan: Devussy Application Framework and Cross‑App Integration
## 1. Context and Motivation

Devussy's web front‑end currently includes a fully working IRC add‑on. This integration:

- Adds an `IrcClient` component and a dedicated `irc` directory with server configuration and documentation.
- Extends the `WindowType` union and window management code to include an `'irc'` type with its own default size and spawn function.
- Updates the taskbar and Start Menu to add an IRC chat entry and to display the current nickname.
- Adds an `ircd` service to `docker-compose.yml` that runs an InspIRCd server with a WebSocket endpoint on port 8080. The client connects via `NEXT_PUBLIC_IRC_WS_URL`, or by default to `/ws/irc/` on the same host. The Nginx configuration proxies `/ws/irc/` to this container.

While this hard‑coded integration works, it couples each new app tightly to the window manager and infrastructure. To support future add‑ons—such as code editors, dashboards or custom microservices—we need a more generic application framework that:

Registers applications dynamically: each app declares its metadata (id, name, icon, default size, route, required services) in a central registry rather than editing multiple files manually.

Supports adding backend services: new apps can define their own Docker containers and Nginx routes without rewriting the core docker-compose.yml and proxy config by hand.

Allows cross‑app communication: data (e.g. generated plans, chat messages, share links) should flow between apps through an event bus or shared context.

Provides deep‑link sharing: users can generate links to pipeline stages or other content that, when clicked (for example from IRC), open the appropriate window and restore state instead of leaving Devussy.

This document lays out a plan to evolve Devussy into a modular, plug‑in based framework and suggests features that demonstrate the power of this approach.

## 2. Goals

Modular App Architecture: define an App interface and registry so new apps can be added without editing core window manager code.

Pluggable Services: allow apps to bundle backend services (e.g. a WebSocket server, file server, AI agent) with declarative configuration for docker-compose and nginx.

Cross‑App Messaging: implement a simple event bus so apps can publish and subscribe to events (e.g. “planReady”, “openShareLink”), enabling decoupled communication.

Share Links: design a consistent link scheme to encode Devussy state (pipeline stages, design/plan data) and intercept those links in the IRC client and other apps to spawn windows with that state.

Ease of Use: provide helper scripts and documentation for developers to create new apps, add services, and define custom UI icons or start‑menu entries.

## 3. High‑Level Architecture

The proposed framework introduces three key layers:

App registry layer: Each add‑on implements an AppDefinition exporting metadata (id, name, icon, default window size, component, optional backend services, environment variables). All definitions are aggregated in a central AppRegistry.

Window manager layer: The existing window manager is updated to derive its window types from the registry. Generic functions spawnAppWindow(appId) and renderAppContent(appId) replace the current switch statements. The taskbar and start menu iterate through the registry to display icons dynamically.

Infrastructure layer: For apps that require a backend, the AppDefinition includes a list of service definitions (Docker image, ports, volumes, environment variables) and proxy rules. A build script composes these snippets into the main docker-compose.yml and Nginx config.

## 4. App Interface and Registry

Define a TypeScript interface (appTypes.ts) for app definitions:

```typescript
export interface AppDefinition {
  id: string;                     // unique identifier (e.g. 'irc', 'pipeline')
  name: string;                   // human‑readable name
  icon: React.ReactNode;          // start menu / desktop icon
  defaultSize: { width: number; height: number };
  startMenuCategory?: string;     // e.g. 'Most Used' or custom category
  component: React.FC<any>;       // main React component to render
  onOpen?: (context: AppContext) => void;  // optional hook when window opens
  services?: DockerServiceDef[];  // optional backend services
  proxy?: NginxProxyDef[];        // optional Nginx rules for this app
  env?: Record<string, string>;   // environment variables for frontend
}

export type DockerServiceDef = {
  name: string;
  image: string;
  ports?: string[];       // e.g. ['8081:80']
  volumes?: string[];
  environment?: Record<string, string>;
  depends_on?: string[];
  restart?: string;
};

export type NginxProxyDef = {
  path: string;           // path prefix, e.g. '/ws/chat/'
  upstream: string;       // service and port, e.g. 'chat:3000'
  websocket?: boolean;    // use WebSocket proxy settings
};

export interface AppContext {
  emit: (event: string, payload?: any) => void;
  subscribe: (event: string, cb: (payload: any) => void) => () => void;
  getState: () => any;
  setState: (patch: any) => void;
}
```

Create an `AppRegistry.ts` that imports each app and exports a map keyed by id:

```typescript
import IrcApp from '@/apps/irc';
import PipelineApp from '@/apps/pipeline';
// future apps...

export const AppRegistry: Record<string, AppDefinition> = {
  [IrcApp.id]: IrcApp,
  [PipelineApp.id]: PipelineApp,
  [HelpApp.id]: HelpApp,
  [ModelSettingsApp.id]: ModelSettingsApp,
  // ...
};
```

**Implementation status – App Interface & Registry (in use by window manager & menus):**

- `devussy-web/src/apps/appTypes.ts` defines `AppDefinition`, `DockerServiceDef`, `NginxProxyDef` and `AppContext` matching this design.
- `devussy-web/src/apps/pipeline.tsx` and `devussy-web/src/apps/irc.tsx` export `AppDefinition` objects for the pipeline (placeholder) and IRC client.
- `devussy-web/src/apps/help.tsx` and `devussy-web/src/apps/modelSettings.tsx` export concrete `AppDefinition` objects for the Help window and the Model Settings window as registry-driven apps.
- `devussy-web/src/apps/AppRegistry.ts` aggregates these definitions into a registry map and also includes placeholder `AppDefinition` entries for the core pipeline windows (`init`, `interview`, `design`, `plan`, `execute`, `handoff`), which are still rendered directly by `page.tsx`.
- `WindowType` in `devussy-web/src/app/page.tsx` is derived from `keyof typeof AppRegistry`, window sizing uses `AppRegistry[appId].defaultSize`, and the Bliss Start menu "All Programs" list is generated from `AppRegistry` using each app's `startMenuCategory`.

The registry and app types are now consumed by the window manager and menus, with IRC, Help, and Model Settings rendered via registry-driven app components. The main pipeline views remain wired directly in `page.tsx` by design, since the pipeline UI is managed as a separate project and is not being fully migrated behind the app framework in this track.

## 5. Cross‑App Communication: Event Bus

To allow independent apps to communicate, implement a simple event bus using a EventEmitter pattern. Create an EventBusContext with emit(eventName, payload) and subscribe(eventName, handler) methods. Provide a useEventBus hook that apps can use.

Example implementation:

```typescript
import { createContext, useContext, useRef } from 'react';

class EventBus {
  private listeners: Record<string, Set<(payload: any) => void>> = {};
  emit(event: string, payload: any) {
    this.listeners[event]?.forEach(fn => fn(payload));
  }
  subscribe(event: string, cb: (payload: any) => void) {
    if (!this.listeners[event]) this.listeners[event] = new Set();
    this.listeners[event].add(cb);
    return () => this.listeners[event].delete(cb);
  }
}

Define a custom URL scheme (or route) that encodes Devussy state in a compact, shareable form. A proposal:

```
devussy://stage=plan&data=<base64‑url‑encoded JSON>
```

Where stage is one of interview, design, plan, execute, handoff, or an identifier defined by the app, and data is a base64‑URL‑safe encoded JSON object containing the relevant state. For example, a plan share link could include { projectName, languages, requirements, design, plan }.

Alternatively, use a web route such as /share?payload=<encoded> so that links are compatible with browsers. When Devussy is open, these links should not navigate away but instead be intercepted by the client.

### 6.2. Generating share links

Add a “Share” button in pipeline views (design/plan/execute) that calls a helper:

```typescript
import { encode } from 'base64url';

function generateShareLink(stage: string, data: any) {
  const payload = encode(JSON.stringify({ stage, data }));
  return `${window.location.origin}/share?payload=${payload}`;
}
```

This function returns a link that can be copied to the clipboard or automatically inserted into the IRC chat via the event bus.

### 6.3. Intercepting share links in the IRC client

Enhance `IrcClient` so that messages are parsed for share links. When rendering a message containing a link that matches the pattern (for example `/share?payload=` or the custom `devussy://` protocol), render it as a clickable element with an `onClick` handler instead of a normal `<a>` tag. The handler should:
- Decode the payload with `JSON.parse(base64url.decode(payload))`.
- Publish an event on the bus, for example `emit('openShareLink', { stage, data })`.

The top‑level page listens for `openShareLink` and calls `spawnAppWindow(stage)` or restores state accordingly. For pipeline stages, reuse the existing `handleLoadCheckpoint` logic to restore `projectName`, `requirements`, `languages`, `design` and `plan`.

### 6.4. Handling share links globally

Also add a catch‑all route in Next.js (pages/share.tsx or app/share/page.tsx) that reads the payload query parameter and, if Devussy is open, forwards the data through the event bus. If the app is not running (e.g. the link is opened in a new tab), display a page with a “Open Devussy” button that loads the main app and passes along the payload.

**Implementation status – Share Links (implemented v1):**

- `devussy-web/src/shareLinks.ts` implements a `ShareLinkPayload` interface together with `generateShareLink(stage, data)` and `decodeSharePayload(encoded)` helpers that use JSON + base64‑URL encoding to produce `/share?payload=...` URLs in a browser‑ and server‑safe way.
- `devussy-web/src/app/share/page.tsx` defines the `/share` route. It reads the `payload` query parameter, validates and decodes it, displays a small summary of the shared stage/project, and persists the raw encoded payload to `sessionStorage` under `devussy_share_payload` before offering an “Open Devussy” button that navigates back to the main desktop.
- `devussy-web/src/components/addons/irc/IrcClient.tsx` parses message text for `/share?payload=` links, renders them as a `[Open shared Devussy state]` button, decodes the payload via the shared helper, and emits an `openShareLink` event on the global event bus when clicked.
- `devussy-web/src/app/page.tsx` subscribes to `openShareLink` on the event bus and also checks `sessionStorage` for a pending `devussy_share_payload` on load. In both cases it turns the embedded `{ projectName, languages, requirements, design, plan, stage }` object into a checkpoint‑like structure and passes it to `handleLoadCheckpoint`, which restores shared state and spawns the appropriate pipeline window (`design`, `plan`, `execute`, or `handoff`).
- `devussy-web/src/components/pipeline/DesignView.tsx`, `PlanView.tsx`, and `ExecutionView.tsx` each expose a “Share” button in their headers. These buttons call `generateShareLink('design' | 'plan' | 'execute', data)` for the respective stage, attempt to copy the URL to the clipboard, and always fall back to showing it in a `window.prompt` so the user can paste it into IRC or elsewhere.
- The same pipeline Share buttons also emit a `shareLinkGenerated` event on the global event bus with `{ stage, data, url }`, and `IrcClient.tsx` listens for this event to post a `[Devussy] Shared <stage> link: <url>` message into `#devussy-chat` whenever a new share link is created.

Remaining work / follow‑ups:

- Decide on and document opinionated share presets (e.g. minimal vs. full project snapshot) and how they relate to backend checkpoints. The current implementation sends a stage‑specific snapshot of the relevant `{ projectName, languages, requirements, design, plan }` fields in the payload.
- Add automated and/or integration tests that cover the end‑to‑end share flow: generating a link, opening it via `/share`, restoring the pipeline state in a new tab, and verifying that the correct window opens for design, plan, and execution stages.

## 7. Compose and Nginx Generation

### 7.1. Service definitions

Each app can define its own services in its AppDefinition:

```json
services: [
  {
    name: 'ircd',
    image: 'inspircd/inspircd-docker:latest',
    ports: ['6667:6667', '8080:8080'],
    volumes: ['./irc/conf/inspircd_v2.conf:/inspircd/conf/inspircd.conf', './irc/logs:/inspircd/logs'],
    restart: 'unless-stopped'
  }
],
proxy: [
  { path: '/ws/irc/', upstream: 'ircd:8080', websocket: true }
],
env: {
  NEXT_PUBLIC_IRC_WS_URL: 'wss://dev.ussy.host/ws/irc/',
  NEXT_PUBLIC_IRC_CHANNEL: '#devussy-chat'
}
```
### 7.2. Build script to merge services

Create a script (scripts/generate-compose.ts) that reads all AppDefinition.services and writes a combined docker-compose.generated.yml. This script should:

Start from a base docker-compose.yml containing frontend, streaming-server and nginx.

Append service definitions from each installed app. Give each service a unique name (e.g. prefix with app id) to avoid collisions.

Terminal / Shell: A web‑based terminal connected to a container with the project files. Useful for advanced users who want to run commands or inspect files manually. Security considerations apply (read‑only or restricted shells).

Kanban / Task Board: Visualize the development plan as cards on a board. Users could reorder phases, assign tasks and track progress. A simple backend could store board state or derive it from the plan JSON.

Feedback Form / Bug Reporter: Allow users to submit feedback or bug reports directly within Devussy. The app could send messages to a serverless function or a GitHub issue via REST.

## 9. Implementation Plan

The work can be broken down into phases. A small team could complete the MVP in 1–2 weeks.

Define types and registry (1 day)

Create appTypes.ts and implement AppDefinition, DockerServiceDef, NginxProxyDef interfaces.

Move the pipeline and IRC functionality into modules under src/apps/pipeline and src/apps/irc, each exporting an AppDefinition.

Implement AppRegistry.ts that aggregates definitions.

Refactor window manager (2–3 days)

Replace hard‑coded WindowType with dynamic keys.

Implement spawnAppWindow and renderAppContent functions.

Update Taskbar and start menu to iterate over the registry.

Verify existing behaviour (pipeline flows, auto‑open IRC) still works.

**Implementation status – Window manager refactor (partial):**

- `WindowType` in `devussy-web/src/app/page.tsx` is now derived from `keyof typeof AppRegistry`.
- Window creation uses `AppRegistry[appId].defaultSize` via `getWindowSize`, matching the previous hard-coded defaults.
- A `spawnAppWindow(appId, ...)` helper wraps the existing `spawnWindow` function and is used by the pipeline and helper actions.
- The `irc`, `help`, and `model-settings` window types now render their content via `AppRegistry[appId].component`, making these apps fully registry-driven while preserving previous behaviour.
- `devussy-web/src/components/window/Taskbar.tsx` now accepts an `onOpenApp(appId)` callback, and both the Bliss Start menu and the non-Bliss floating taskbar use it to launch apps by id. `devussy-web/src/app/page.tsx` maps known app ids to existing handlers and falls back to `AppRegistry[appId]` for unknown ones.
- The Bliss Start menu's **All Programs** list is generated from `AppRegistry` using each app's `startMenuCategory`, while the **Most Used** entries remain curated but still launch apps via their registry ids.
- `renderAppContent` in `devussy-web/src/app/page.tsx` now includes a generic `default` branch that renders any app whose `AppRegistry[appId]` entry provides a `component`. The main pipeline windows (`init`, `interview`, `design`, `plan`, `execute`, `handoff`) deliberately continue to use bespoke branches in `page.tsx`, since the pipeline UI is treated as a separate project and is not being refactored behind the app framework in this DevPlan.

Event bus implementation (0.5 day)

Implement EventBusContext and useEventBus hook.

Update page.tsx to provide the context and pass an AppContext to each app.

Replace direct callback props where appropriate (e.g. sending notifications) with event bus messages.

Share link feature (2–3 days)

Implement generateShareLink helper and add “Share” buttons in design/plan/execute views.

Parse share links in IrcClient and intercept clicks.

Add a global share route to handle payloads when Devussy isn’t open.

Use the event bus to restore pipeline state and spawn windows.

Compose and Nginx generation (2 days)

Write scripts/generate-compose.ts to merge service definitions and update docker-compose.generated.yml and nginx/conf.d/apps.conf.

Add a build step to regenerate these files during CI or whenever the compose generator script is executed (for example via a dedicated npm script or a manual `npx ts-node scripts/generate-compose.ts` invocation).

Document how to define new services and proxies in README.md.

Migration and testing (2 days)

Migrate existing docker-compose.yml to the generated version and test locally.

Write tests to ensure share links open correct windows and restore data correctly.

Test cross‑app events (e.g. pipeline sending notifications to IRC, or other apps).

## 10. Considerations and Safety

Security: Exposing additional services via Nginx requires careful configuration (TLS termination, authentication where necessary). Never expose services that store secrets without proper access control. Avoid sharing API keys or tokens through share links.

Performance: Each new container increases resource usage. Limit the number of services running by default and make optional apps lazy‑loaded. Provide guidelines for scaling horizontally.

Backwards compatibility: For existing installations without the new framework, continue to support the hard‑coded 'irc' integration until the migration is complete. Provide migration notes in the repository.

User experience: Ensure the start menu and desktop icons remain uncluttered. Use categories and search to help users discover apps. Document the share link feature clearly in the help documentation.

## 11. Conclusion

By abstracting application metadata into a registry, introducing an event bus for cross‑app communication, and generating infrastructure configuration from declarative definitions, Devussy becomes a flexible platform for hosting a wide range of tools. The IRC add‑on is the first of many; with the proposed framework, adding a new app—whether a chat client, a code viewer or an AI companion—requires only a small, self‑contained module and a service definition. The share‑link feature enriches collaboration by allowing users to jump directly into any stage of a project from within chat. These enhancements will enable Devussy to grow into a true developer desktop in the browser.