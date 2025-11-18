# Devussy Frontend Implementation Plan

This plan outlines the steps to build a Next.js-based frontend for Devussy, hosted on Vercel, with a premium UI, multi-window streaming, and GitHub integration.

## Architecture Overview

- **Framework**: Next.js 14+ (App Router) with TypeScript.
- **Styling**: Tailwind CSS + Shadcn UI (for premium, accessible components) + Framer Motion (for animations).
- **Backend**: Next.js API Routes (Python) to interface with the existing `src/pipeline` logic.
- **State Management**: React Context + Zustand (for window/phase state).
- **Streaming**: Server-Sent Events (SSE) or direct HTTP streaming for real-time feedback.
- **Deployment**: Vercel.

## Phase 1: Project Initialization & UI Foundation

1.  **Initialize Next.js Project**
    - Create new Next.js app: `npx create-next-app@latest devussy-web --typescript --tailwind --eslint`.
    - Configure `next.config.js` to support Python API routes (rewrites/builds).
    - Install dependencies: `lucide-react` (icons), `framer-motion` (animations), `clsx`, `tailwind-merge`.

2.  **Setup Design System (Premium UI)**
    - Install Shadcn UI base: `npx shadcn-ui@latest init`.
    - Add components: `card`, `button`, `input`, `textarea`, `dialog`, `scroll-area`, `resizable` (for windows).
    - Define a custom dark-mode theme in `globals.css` (deep blues/purples/blacks for a "hacker/dev" aesthetic).
    - Create a `Layout` component with a glassmorphism header and dynamic background.

3.  **Implement Window Manager**
    - Create a `WindowManager` component using `react-grid-layout` or a custom flex/grid solution with `framer-motion`.
    - Features:
        - **Draggable**: Windows can be moved (optional, but nice).
        - **Resizable**: Users can adjust width/height.
        - **Minimizable**: Windows collapse to a taskbar or header.
        - **Focus**: Clicking a window brings it to z-index front.
    - Create a `WindowFrame` component that wraps content with these controls.

## Phase 2: Backend API Adaptation (Python)

*Goal: Expose the existing pipeline logic as stateless API endpoints.*

4.  **Setup Python Runtime on Vercel**
    - Configure `api/` directory for Python serverless functions.
    - Ensure `requirements.txt` includes `devussy` dependencies (or vendor them if needed).
    - **Crucial**: Ensure API keys (OpenAI/Requesty) are accessible via environment variables.

5.  **API: Project Design (`/api/design`)**
    - Endpoint that accepts `requirements`, `languages`, etc.
    - Runs `ProjectDesignGenerator`.
    - **Streaming**: Streams the markdown output chunk by chunk.

6.  **API: Basic Plan (`/api/plan/basic`)**
    - Endpoint accepting the *approved* Project Design JSON.
    - Runs `BasicDevPlanGenerator`.
    - Returns the list of phases (JSON) + Summary.

7.  **API: Phase Detail (`/api/plan/detail`)**
    - Endpoint accepting `BasicDevPlan` context + `PhaseNumber`.
    - Runs `DetailedDevPlanGenerator` for *just that phase*.
    - **Streaming**: Streams the detailed steps for that specific phase.
    - *Note*: This allows the frontend to trigger N parallel requests for N phases, solving the Vercel timeout issue and enabling multi-window streaming.

8.  **API: Handoff & GitHub (`/api/handoff`, `/api/github/create`)**
    - `handoff`: Generates final prompt.
    - `github/create`: Accepts a GitHub token + repo name + file tree. Uses `PyGithub` or REST API to create repo and push files.

## Phase 3: Core Pipeline UI Implementation

9.  **Step 1: Input & Interview**
    - Create a landing page with a "terminal-like" input form.
    - Fields: Project Name, Languages, Requirements (Textarea).
    - "Start" button triggers transition to Design phase.

10. **Step 2: Design Generation & Review**
    - View: A central streaming window showing the Architecture/Tech Stack.
    - **Interaction**:
        - Stream finishes.
        - User can click "Edit" to modify the markdown directly.
        - User clicks "Approve & Plan" to proceed.

11. **Step 3: Basic Plan Generation**
    - View: Displays the list of generated phases.
    - **Interaction**:
        - User can add/remove/rename phases before "Detailed Generation".
        - "Generate Details" button triggers the multi-window view.

12. **Step 4: Multi-Window Detailed Generation**
    - **Logic**: Iterate through phases. For each phase, spawn a `WindowFrame` and trigger a `fetch` to `/api/plan/detail`.
    - **Visual**:
        - Grid of windows appears, one for each phase.
        - All windows stream content simultaneously (matrix style).
        - User can maximize a specific phase to read details.
        - User can minimize completed phases.
    - **Refinement**:
        - Add a "Regenerate" button on each window to re-run just that phase with new instructions (Re-interview).

## Phase 4: Finalization & Export

13. **Handoff & Assembly**
    - Once all phases are done, show "Handoff" window.
    - Generate the final `handoff_prompt.md`.

14. **Download Feature**
    - Implement `JSZip` logic.
    - Button "Download .zip":
        - Bundles `project_design.md`, `devplan.md`, `handoff_prompt.md`, and individual phase files.
        - Triggers browser download.

15. **GitHub Integration**
    - "Push to GitHub" button.
    - Input field for Personal Access Token (PAT) or OAuth flow (if configured).
    - Input for "Repository Name".
    - Calls `/api/github/create` to push the artifacts.

## Phase 5: Polish & Deployment

16. **Error Handling & Recovery**
    - Handle API timeouts or failures gracefully (retry buttons on windows).
    - "Baked-in Keys": Ensure the `.env` on Vercel is set up with the user's keys for this demo instance.

17. **Visual Polish**
    - Add CRT scanline effects or "matrix" rain (optional, low opacity) for the background.
    - Ensure typography is monospaced for code/plans (e.g., `JetBrains Mono`).

18. **Deploy**
    - Push to Vercel.
    - Verify Python runtime cold starts and streaming performance.
