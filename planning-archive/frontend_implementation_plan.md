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

9.  **Step 1: Interactive Interview (Implemented)**
    - **View**: `InterviewView` component.
    - **Logic**: Chat interface using `/api/interview`.
    - **Transition**: On completion, spawns the Design window while keeping the Interview window open for reference.

10. **Step 2: Design Generation & Review (Implemented)**
    - **View**: `DesignView` component.
    - **Logic**: Streams `ProjectDesignGenerator` output using SSE.
    - **Status**: **Complete**.
    - **Streaming Fix**: Uses direct connection to backend (port 8000) to bypass Next.js proxy buffering. `RequestyClient` updated to handle async callbacks correctly.
    - **Button Fix (2025-11-18)**: Added explicit `return` statement in stream handler when `done` message is received to ensure `isGenerating` is set to false immediately, enabling the "Approve & Plan" button.
    - **Interaction**:
        - Stream finishes and "Approve & Plan" button is enabled.
        - User can click "Edit" to modify the markdown directly.
        - User clicks "Approve & Plan" to spawn the Plan window.

11. **Step 3: Basic Plan Generation + Phase Editing (Implemented)**
    - **View**: `PlanView` component.
    - **Logic**: Streams `BasicDevPlanGenerator` output using SSE to prevent connection timeouts.
    - **Status**: **Complete** with major UX enhancements (2025-11-18 Night).
    - **Streaming Implementation**: Switched from blocking JSON response to SSE streaming in `api/plan/basic.py`.
    - **Phase Editing Features (NEW)**:
        - **PhaseCard Component**: Reusable component for individual phase management
        - **Card View**: Displays phases as editable cards with expand/collapse
        - **Raw Text View**: Toggle to edit full devplan text directly
        - Phases **expand by default** for easy editing
        - **Add/Edit/Delete/Reorder** phases individually
        - Changes persist when user clicks "Approve & Start Execution"
    - **Files**: 
        - `src/components/pipeline/PlanView.tsx` (MAJOR REFACTOR)
        - `src/components/pipeline/PhaseCard.tsx` (NEW)
    - **Interaction**:
        - Devplan streams in with real-time text display
        - After streaming: User sees editable phase cards (or can toggle to raw text)
        - User can modify, add, remove, and reorder phases
        - "Approve & Start Execution" button triggers multi-phase execution window

12. **Step 4: Multi-Window Execution with Grid View (Implemented)**
    - **Architecture**: `page.tsx` manages a list of `windows` state.
    - **Status**: **Implemented** but has lint errors (see Known Issues below).
    - **View**: `ExecutionView` component (NEW) - Replaces single-phase `PhaseDetailView`
    - **Features**:
        - **Grid View** (default): 3-column grid showing all phases simultaneously
        - **Tabs View** (toggle): Focus on one phase at a time
        - **Auto-start**: Execution begins automatically when window opens
        - **Concurrency Control**: Dropdown to select 1, 2, 3, 5, or All concurrent phases (default: 3)
        - **Pause/Resume**: Control execution flow
        - **Full Streaming Output**: Real-time terminal output for each phase
        - **Visual Status Indicators**:
            - ⟳ Running (blue)
            - ✓ Complete (green)
            - ✗ Failed (red)
            - ⏰ Queued (gray)
        - **Progress Tracking**: Visual progress bars and completion counter
    - **Files**:
        - `src/components/pipeline/ExecutionView.tsx` (NEW)
        - `src/app/page.tsx` (UPDATED to use ExecutionView)
        - `api/plan/detail.py` (FIXED - was incomplete)
    - **Known Issues**: ⚠️ Lint errors need fixing before testing:
        - ExecutionView has syntax errors (missing return, incorrect ref callback, Select component import)
        - page.tsx has corrupted execute case (needs reconstruction)
        - See `handoff.md` "Known Issues" section for full details
    - **Visual**:
        - Windows stack with z-index management (click to focus)
        - Previous windows (Interview, Design, Plan) remain accessible
        - Grid layout provides at-a-glance view of all phase progress

## Global Changes (2025-11-18 Night)
- **Default Model**: Changed from `gpt-4o` to `gpt-5-mini` in `src/app/page.tsx`
- **API Fixes**: Fixed `/api/plan/detail.py` (had undefined variables, now properly initializes generator)

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
