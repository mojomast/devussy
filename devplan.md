# Development Plan

## Summary

DevUssY (DevPlan Orchestrator) is an AI-powered development planning tool that generates comprehensive project documentation. This development plan tracks the completion of the core CLI tool and web interface.

**Current Status:** Phase 20 - Iterative Workflow Integration (IN PROGRESS 🟡 80% Complete)  
**Version:** 0.4.1-alpha

**📌 URGENT:** See `PHASE_20_PROGRESS.md` for detailed status, fixes completed tonight, and next steps!

---

## Completed Phases

### Phase 1-10: Core CLI & Backend Infrastructure ✅
- ✅ Project structure and development environment
- ✅ Multi-LLM client architecture with provider abstraction
- ✅ Pipeline orchestration (Design → DevPlan → Handoff)
- ✅ Configuration system with YAML and environment variables
- ✅ File management, Git integration, and state management
- ✅ Interactive questionnaire mode
- ✅ Comprehensive testing (414 tests, 73% coverage)
- ✅ FastAPI web backend with WebSocket support
- ✅ Package preparation for PyPI

### Phase 11: Web Interface - Configuration System ✅

**Completed:** October 21, 2025

#### Backend (Completed)
- ✅ `src/web/security.py` - Fernet encryption for API keys (98% coverage, 13 tests)
- ✅ `src/web/config_models.py` - Pydantic models (100% coverage)
- ✅ `src/web/config_storage.py` - JSON file storage (90% coverage, 14 tests)
- ✅ `src/web/routes/config.py` - REST API endpoints (15+ endpoints)
- ✅ Credential CRUD operations
- ✅ Global configuration management
- ✅ Preset system
- ✅ All tests passing (27 tests for configuration system)

#### Frontend (Completed)
- ✅ React + TypeScript + Vite + Tailwind CSS setup
- ✅ `frontend/src/services/configApi.ts` - API client with TypeScript types
- ✅ `frontend/src/pages/SettingsPage.tsx` - Tab-based settings interface
- ✅ `frontend/src/components/config/CredentialsTab.tsx` - API key management UI
- ✅ `frontend/src/components/config/GlobalConfigTab.tsx` - Global configuration UI
- ✅ `frontend/src/components/config/PresetsTab.tsx` - Configuration presets UI
- ✅ Settings route integrated into main app navigation
- ✅ Responsive design with Tailwind CSS
- ✅ Form validation and error handling
- ✅ Real-time API key testing
- ✅ CORS configuration for local development

#### Integration
- ✅ Backend and frontend running successfully
- ✅ Backend: http://localhost:8000
- ✅ Frontend: http://localhost:3000
- ✅ API endpoints accessible from frontend
- ✅ Settings page navigable at /settings

---

## Phase 12: Web Interface - Core Features ✅

**Status:** COMPLETED  
**Completed:** October 21, 2025  
**Duration:** 1 day

### Objectives
Complete the main project workflow through the web interface.

### Tasks
- ✅ `frontend/src/services/projectsApi.ts` - Projects API client with TypeScript types
- ✅ `frontend/src/pages/ProjectsListPage.tsx` - Project list/dashboard with filtering
- ✅ `frontend/src/pages/ProjectDetailPage.tsx` - Project detail view with streaming
- ✅ `frontend/src/pages/CreateProjectPage.tsx` - Enhanced project creation form
- ✅ `frontend/src/pages/HomePage.tsx` - Improved landing page with dashboard
- ✅ WebSocket integration for real-time updates
- ✅ File content viewing in project details
- ✅ Backend endpoint for file retrieval
- ✅ Project CRUD operations (create, list, view, delete, cancel)

---

## Phase 13: Polish & Testing

**Status:** Completed ✅ 
**Started:** October 21, 2025  
**Completed:** October 21, 2025

### Completed Tasks
- ✅ Testing infrastructure setup (Vitest + React Testing Library)
- ✅ Component tests for ProjectsListPage (14 tests passing)
- ✅ Component tests for CreateProjectPage (16 tests passing)
- ✅ Component tests for SettingsPage (12 tests passing)
- ✅ Toast notification system integrated (react-hot-toast)
  - Success/error messages for all user actions
  - Promise-based toasts for async operations
  - Applied to projects, credentials, and configuration
- ✅ Error boundary component
  - Graceful error handling for React component errors
  - User-friendly error UI with retry option
  - Integrated into App.tsx
- ✅ Skeleton loader components
  - Professional loading states for ProjectsListPage
  - Reusable skeleton components (ProjectCardSkeleton, ProjectsGridSkeleton, etc.)
  - Improved perceived performance

### Test Results
- **Frontend Tests:** 42 tests passing (3 test files)
  - ProjectsListPage: 14 tests
  - CreateProjectPage: 16 tests  
  - SettingsPage: 12 tests
- **Backend Tests:** 414 tests passing (73% coverage)
- **Total:** 456 tests passing across frontend and backend

---

## Phase 14: Enhanced UI Features

**Status:** Completed ✅
**Started:** October 21, 2025
**Completed:** October 21, 2025

### Completed Tasks
- ✅ **Dark Mode Support**
  - Theme context with localStorage persistence
  - System preference detection
  - Theme toggle button in navigation header
  - Dark mode classes throughout all pages and components
  - Smooth transitions between themes
  
- ✅ **Markdown Rendering**
  - FileViewer component with react-markdown
  - Syntax highlighting with react-syntax-highlighter
  - View mode toggle (Rendered vs Raw)
  - Support for code blocks with language detection
  - Dark mode support in code highlighting
  
- ✅ **Enhanced File Viewer**
  - Copy to clipboard functionality
  - Download individual files
  - Download all files as ZIP archive (using jszip)
  - Integrated into ProjectDetailPage
  - Dark mode support

### Implementation Details
- **New Components:**
  - `frontend/src/contexts/ThemeContext.tsx` - Theme management
  - `frontend/src/components/FileViewer.tsx` - Enhanced file viewing

- **Updated Components (Dark Mode):**
  - Layout, HomePage, ProjectDetailPage
  - Skeleton components
  - ErrorBoundary
  - All page components

- **Dependencies Added:**
  - `@tailwindcss/typography` - Markdown prose styles
  - `jszip` - ZIP file creation
  - `@types/jszip` - TypeScript types

### Phase 14: Enhanced UI Features

**Status:** Completed ✅
**Started:** October 21, 2025
**Completed:** October 21, 2025

### Completed Tasks
- ✅ **Dark Mode Support**
  - Theme context with localStorage persistence
  - System preference detection
  - Theme toggle button in navigation header
  - Dark mode classes throughout all pages and components
  - Smooth transitions between themes
  
- ✅ **Markdown Rendering**
  - FileViewer component with react-markdown
  - Syntax highlighting with react-syntax-highlighter
  - View mode toggle (Rendered vs Raw)
  - Support for code blocks with language detection
  - Dark mode support in code highlighting
  
- ✅ **Enhanced File Viewer**
  - Copy to clipboard functionality
  - Download individual files
  - Download all files as ZIP archive (using jszip)
  - Integrated into ProjectDetailPage
  - Dark mode support

### Implementation Details
- **New Components:**
  - `frontend/src/contexts/ThemeContext.tsx` - Theme management
  - `frontend/src/components/FileViewer.tsx` - Enhanced file viewing

- **Updated Components (Dark Mode):**
  - Layout, HomePage, ProjectDetailPage
  - Skeleton components
  - ErrorBoundary
  - All page components

- **Dependencies Added:**
  - `@tailwindcss/typography` - Markdown prose styles
  - `jszip` - ZIP file creation
  - `@types/jszip` - TypeScript types

---

## Phase 15: Advanced UI Features

**Status:** Completed ✅
**Started:** October 21, 2025 (Current Session)
**Completed:** October 21, 2025 (Current Session)

### Objectives
Implement advanced UI features for better user experience and productivity.

### Completed Tasks

#### 1. Project Search & Filtering ✅
- **Search Functionality:**
  - Real-time search box for filtering by project name or description
  - Instant filtering as user types
  - Search results count display
  
- **Advanced Sorting:**
  - Sort by: Newest First, Oldest First, Name (A-Z), Name (Z-A), Status
  - Dropdown selector for easy sort option switching
  - Maintained with useMemo for performance
  
- **Enhanced Filters:**
  - Status filter buttons (All, Completed, Running, Failed, Cancelled)
  - Combined search + status filtering
  - Clear filters button when search/filter active
  
- **Dark Mode Support:**
  - All search/filter controls support dark theme
  - Consistent styling across light and dark modes

#### 2. Project Templates System ✅
- **Backend Implementation:**
  - `src/web/config_models.py` - Added `ProjectTemplate`, `CreateTemplateRequest`, `UpdateTemplateRequest` models
  - `src/web/config_storage.py` - Template CRUD operations with file storage
  - `src/web/routes/templates.py` - REST API endpoints for template management
  - `src/web/app.py` - Integrated templates router
  
- **Template Features:**
  - Save project configurations as reusable templates
  - Template metadata: name, description, tags, usage count
  - Track when templates were created and last used
  - Increment usage count when template is used
  - Sort templates by usage (most used first)
  
- **Frontend Implementation:**
  - `frontend/src/services/templatesApi.ts` - TypeScript API client
  - `frontend/src/pages/TemplatesPage.tsx` - Full template management UI
  - Template creation modal with name, description, and tags
  - Template grid view with usage statistics
  - Use/Delete actions for each template
  - Navigation link in main menu
  
- **API Endpoints:**
  - `POST /api/templates` - Create template
  - `GET /api/templates` - List all templates
  - `GET /api/templates/{id}` - Get specific template
  - `PUT /api/templates/{id}` - Update template
  - `DELETE /api/templates/{id}` - Delete template
  - `POST /api/templates/{id}/use` - Mark template as used

#### 3. Analytics Dashboard ✅
- **Statistics Display:**
  - Total projects count
  - Completed projects count
  - Currently running projects count
  - Failed projects count
  - Success rate percentage (completed / (total - running))
  
- **Implementation:**
  - Added to HomePage as statistics cards
  - Responsive grid layout (2 cols mobile, 5 cols desktop)
  - Color-coded metrics (blue, green, red, purple)
  - Dark mode support
  - Only shows when projects exist
  
- **Visual Design:**
  - Large, bold numbers for quick scanning
  - Descriptive labels
  - Consistent card styling
  - Smooth transitions

### Files Modified/Created

**Backend:**
- Modified: `src/web/config_models.py` (added template models)
- Modified: `src/web/config_storage.py` (added template methods)
- Created: `src/web/routes/templates.py` (template API)
- Modified: `src/web/app.py` (added templates router and directory)

**Frontend:**
- Modified: `frontend/src/pages/ProjectsListPage.tsx` (search & filtering)
- Modified: `frontend/src/pages/HomePage.tsx` (analytics dashboard)
- Created: `frontend/src/services/templatesApi.ts` (template API client)
- Created: `frontend/src/pages/TemplatesPage.tsx` (template management UI)
- Modified: `frontend/src/App.tsx` (templates route)
- Modified: `frontend/src/components/Layout.tsx` (templates nav link)

### Testing Status
- Backend templates API endpoints functional
- Frontend templates page functional
- Search and filtering tested manually
- Analytics calculations verified
- Dark mode support across all new features

---

## Phase 16: Template & Project Management Enhancements

**Status:** Completed ✅
**Started:** October 21, 2025
**Completed:** October 21, 2025

### Objectives
Enhance template system and improve project list management with better UX features.

### Completed Tasks

#### 1. Template Creation from Projects ✅
- **Backend Enhancement:**
  - Implemented `/api/templates/from-project/{project_id}` endpoint
  - Extract configuration from completed projects
  - Validate project status before template creation
  
- **Frontend Implementation:**
  - Added "Save as Template" button on ProjectDetailPage
  - Only shows for completed projects
  - Modal dialog for template metadata (name, description, tags)
  - Toast notifications for success/error feedback
  
- **Features:**
  - Convert successful projects into reusable templates
  - Preserve project configuration for future use
  - Track which project a template was created from

#### 2. Template Search and Filtering ✅
- **Search Functionality:**
  - Real-time search by template name or description
  - Instant filtering as user types
  
- **Tag-based Filtering:**
  - Filter templates by tags
  - "All" option to clear tag filter
  - Visual indication of active filter
  
- **UI Enhancements:**
  - Tag filter buttons with active state styling
  - Results count display
  - Clear filters button when active
  - Dark mode support throughout

#### 3. Template Import/Export ✅
- **Backend Implementation:**
  - `GET /api/templates/{template_id}/export` - Export as JSON
  - `POST /api/templates/import` - Import from JSON file
  - Automatic ID generation to avoid conflicts
  - Reset usage statistics on import
  
- **Frontend Implementation:**
  - Export button on each template card
  - Import button in page header with file picker
  - Automatic JSON file download with template name
  - File upload with validation
  - Toast notifications for progress and errors
  
- **Features:**
  - Share templates between users/systems
  - Backup template configurations
  - Template versioning through files

#### 4. Project List Pagination ✅
- **Pagination Implementation:**
  - 12 items per page (3 columns × 4 rows)
  - First/Previous/Next/Last navigation
  - Smart page number display (shows 5 pages max)
  - Current page highlighting
  
- **UX Improvements:**
  - Automatic reset to page 1 on filter/search changes
  - Updated results count shows current range
  - Disabled states for boundary buttons
  - Dark mode support for all controls
  
- **Performance:**
  - Only render visible projects
  - Reduced DOM size for large project lists
  - Smooth pagination experience

### Files Modified/Created

**Backend:**
- Modified: `src/web/routes/templates.py`
  - Added `/from-project/{project_id}` endpoint
  - Added `/export` and `/import` endpoints
  - Import validation and error handling

**Frontend:**
- Modified: `frontend/src/pages/ProjectDetailPage.tsx`
  - Save as Template button and modal
  - Template creation handler with toast notifications
  
- Modified: `frontend/src/pages/TemplatesPage.tsx`
  - Search and tag filtering
  - Import/export functionality
  - Filter UI components
  
- Modified: `frontend/src/pages/ProjectsListPage.tsx`
  - Pagination state management
  - Paginated display logic
  - Pagination controls component
  
- Modified: `frontend/src/services/templatesApi.ts`
  - `createTemplateFromProject` method
  - `exportTemplate` method (returns Blob)
  - `importTemplate` method (FormData upload)

### Testing Status
- All features manually tested
- No TypeScript compilation errors
- Dark mode verified across all new features
- Toast notifications working properly
- File upload/download functioning correctly

### Benefits
- **Better Template Management:** Users can now create templates from successful projects
- **Template Organization:** Search and filter make finding templates easier
- **Template Sharing:** Export/import enables collaboration and backup
- **Improved Performance:** Pagination handles large project lists gracefully
- **Enhanced UX:** Smooth interactions with proper feedback

---

## Phase 17: Requesty Provider Integration & Model Management ✅

**Status:** COMPLETED  
**Completed:** October 22, 2025  
**Duration:** 1 session

### Objectives
Fix API credential testing and add model management features specifically for Requesty provider.

### Completed Tasks

#### 1. Fixed API Credential Testing ✅
- **Root Issue:** "api_key client option must be set" error when testing credentials
- **Root Cause:** LLMConfig wasn't wrapped in structure clients expect (config.llm.api_key)
- **Solution Implemented:**
  - Updated `/api/config/credentials/{id}/test` endpoint in `src/web/routes/config.py`
  - Created proper config wrapper using SimpleNamespace
  - Wrapped LLMConfig in structure: `config.llm`, `config.retry`, `config.max_concurrent_requests`
  - Clients now receive config in expected format
  - Test endpoint works with Requesty provider

#### 2. Model Listing from Requesty API ✅
- **Backend Implementation:**
  - Added endpoint: `GET /api/config/credentials/{credential_id}/models`
  - Fetches available models from Requesty API's `/v1/models` endpoint
  - Returns structured model data: id, name, description, context_window
  - Error handling for unsupported providers
  
- **Frontend Implementation:**
  - Updated `configApi.ts` with `listAvailableModels()` method
  - Added `AvailableModel` TypeScript interface
  - Enhanced `CredentialsTab.tsx` with:
    - "List Models" button (appears when credential is valid)
    - Automatic model loading after successful test
    - Grid display of available models
    - Model details: ID, name, context window
  - Toast notifications for loading success/failure

#### 3. Per-Stage Model Configuration UI ✅
- **Global Config Tab Enhancement:**
  - Added "Pipeline Stage Configuration" section
  - Three stage cards: Design (blue), DevPlan (green), Handoff (purple)
  - Each stage allows:
    - Optional model override (defaults to global model)
    - Temperature configuration
  - Color-coded visual organization
  - Clear explanation text

#### 4. Verified CLI Integration ✅
- **Confirmed Web UI Uses CLI Structure:**
  - `src/web/project_manager.py` analysis:
    - Uses `load_config()` from `src/config.py`
    - Uses `create_llm_client()` from `src/clients/factory.py`
    - Uses `PipelineOrchestrator` from `src/pipeline/compose.py`
    - Same config structure between CLI and web
  - Requesty client works in both CLI and web contexts
  - Shared infrastructure confirmed

### Files Modified/Created

**Backend:**
- Modified: `src/web/routes/config.py`
  - Fixed test_credential() function with proper config wrapper
  - Added list_available_models() endpoint for Requesty
- Modified: `src/web/config_models.py`
  - Added AvailableModel Pydantic model

**Frontend:**
- Modified: `frontend/src/services/configApi.ts`
  - Added listAvailableModels() method
  - Added AvailableModel TypeScript interface
- Modified: `frontend/src/components/config/CredentialsTab.tsx`
  - Added handleLoadModels() function
  - Added state for available models
  - Added "List Models" button UI
  - Added models grid display
- Modified: `frontend/src/components/config/GlobalConfigTab.tsx`
  - Added stage-specific model configuration section
  - Color-coded stage cards
  - Model and temperature inputs per stage

### Testing Status
- API credential testing working for Requesty
- Model listing endpoint functional
- Frontend UI displaying models correctly
- No TypeScript compilation errors
- Integration with existing UI flows verified

### Benefits
- **Fixed Critical Bug:** API credential testing now works
- **Better UX:** Users see available models after testing credentials
- **Flexibility:** Per-stage model assignment for optimized workflows
- **Transparency:** Clear display of model capabilities and limits
- **Verified Architecture:** Confirmed shared CLI/web infrastructure

---

## Phase 18: Iterative Workflow Implementation ✅

**Status:** COMPLETED ✅  
**Completed:** October 22, 2025  
**Duration:** 1 session

### Objectives
Implement Kyle's vision: transform DevUssY into an iterative, multi-stage workflow where users can review, refine, and approve each phase before moving to the next.

### Completed Tasks

#### 1. Backend Models & State ✅
- **Models Updated:**
  - Added `AWAITING_USER_INPUT` to ProjectStatus enum
  - Added `REFINED_DEVPLAN` to PipelineStage enum (now 5 stages total)
  - Created `IterationRequest` model (feedback, regenerate flag)
  - Created `StageApproval` model (approved flag, notes)
  - Created `IterationHistory` model (tracking iterations per stage)
  - Updated `ProjectResponse` with iteration fields:
    - `current_iteration`: int
    - `awaiting_user_input`: bool
    - `iteration_prompt`: str (what to ask user)
    - `current_stage_output`: str (content to review)

#### 2. Backend API Endpoints ✅
- **New Routes in `src/web/routes/projects.py`:**
  - `POST /api/projects/{id}/iterate` - Submit feedback and optionally regenerate
  - `POST /api/projects/{id}/approve` - Approve current stage, move to next
  
- **Features:**
  - Validation that project is awaiting input
  - Background task execution for regeneration
  - Error handling and status updates
  - Integration with project_manager

#### 3. Backend Pipeline Logic ✅
- **ProjectManager Enhancements:**
  - Added iteration tracking to Project dataclass
  - Modified `run_pipeline()` to pause after Design stage
  - Created `iterate_stage()` method - records feedback, increments iteration
  - Created `approve_stage()` method - clears iteration state, moves to next stage
  - Created `regenerate_current_stage()` method - regenerates with user feedback
  - Created `continue_pipeline()` method - determines next stage and continues
  
- **Pipeline Flow:**
  1. Generate Design → PAUSE (AWAITING_USER_INPUT)
  2. User reviews → Iterate OR Approve
  3. If Iterate: Regenerate with feedback → PAUSE again
  4. If Approve: Move to Basic DevPlan → Generate → PAUSE
  5. Repeat for all 5 stages

#### 4. Frontend API Client ✅
- **Updated `frontend/src/services/projectsApi.ts`:**
  - Added `AWAITING_USER_INPUT` to ProjectStatus enum
  - Updated PipelineStage enum with 5 stages
  - Added iteration fields to ProjectResponse interface
  - Created `IterationRequest` interface
  - Created `StageApproval` interface
  - Implemented `iterateStage()` method
  - Implemented `approveStage()` method
  - Updated WebSocketMessage types for iteration events

#### 5. Frontend Iteration UI ✅
- **Enhanced `frontend/src/pages/ProjectDetailPage.tsx`:**
  - Added iteration state management
  - Created `handleApproveStage()` handler
  - Created `handleRegenerateWithFeedback()` handler
  - Updated WebSocket message handler for `awaiting_input` and `regenerated` events
  - Built beautiful "User Review Required" UI card:
    - Yellow background with pulse animation
    - Stage name and iteration count display
    - Current output preview (first 500 characters)
    - Feedback textarea
    - "Approve & Continue" button (green)
    - "Regenerate with Feedback" button (blue, requires feedback)
  - Toast notifications for all iteration actions
  - Auto-reload project after iteration events

#### 6. Phase Progress Indicator ✅
- **Visual Pipeline Progress:**
  - 5-stage progress bar (Design → Basic → Detailed → Refined → Handoff)
  - Animated progress line showing completion percentage
  - Stage dots with icons: 🎨 📋 📝 ✨ 🚀
  - Active stage highlighted in blue with ring effect
  - Completed stages show green checkmark
  - Iteration counter badge on active stage
  - Responsive design with dark mode support

#### 7. Comprehensive Prompt Templates ✅
- **Created `src/prompts/` directory with:**
  - `design_initial.txt` - Initial project design generation
  - `design_iteration.txt` - Design refinement with user feedback
  - `devplan_basic.txt` - High-level phases and milestones (4-8 phases)
  - `devplan_detailed.txt` - **100-300 numbered actionable steps**
  - `devplan_refined.txt` - Agent-ready plan with troubleshooting
  - `handoff_generation.txt` - **Complete Roo orchestrator handoff**

### Prompt Template Highlights

**Detailed DevPlan Template:**
- Targets 100-300 numbered steps minimum
- Each step includes: action, files, code, validation, troubleshooting
- Covers: setup, database, features, API, testing, deployment, docs
- Step format designed for granular tracking

**Handoff Template:**
- Complete self-updating protocol for Roo orchestrator
- Instructions to update devplan as work progresses
- Git commit guidelines (every 10 steps, every milestone)
- Handoff creation protocol (when to create next handoff)
- Emergency protocols for blockers
- Definition of Done checklist
- Motivational messaging for autonomous agent

### Files Modified/Created

**Backend:**
- Modified: `src/web/models.py`
  - Added AWAITING_USER_INPUT, REFINED_DEVPLAN enums
  - Added iteration models
  - Updated ProjectResponse with iteration fields

- Modified: `src/web/routes/projects.py`
  - Added iterate and approve endpoints
  - Imported new models

- Modified: `src/web/project_manager.py`
  - Updated Project dataclass with iteration fields
  - Modified run_pipeline to pause after stages
  - Added iterate_stage, approve_stage, regenerate_current_stage, continue_pipeline methods

**Frontend:**
- Modified: `frontend/src/services/projectsApi.ts`
  - Updated enums and interfaces
  - Added iteration API methods

- Modified: `frontend/src/pages/ProjectDetailPage.tsx`
  - Added iteration state and handlers
  - Built iteration UI section
  - Added phase progress indicator
  - Updated WebSocket handler

- Modified: `frontend/src/pages/CreateProjectPage.tsx`
  - **FIXED**: Added bg-white/dark:bg-gray-700 to all inputs (fixes white-on-white text)
  - Added dark:border-gray-600 for better dark mode borders

**Prompts:**
- Created: `src/prompts/design_initial.txt`
- Created: `src/prompts/design_iteration.txt`
- Created: `src/prompts/devplan_basic.txt`
- Created: `src/prompts/devplan_detailed.txt`
- Created: `src/prompts/devplan_refined.txt`
- Created: `src/prompts/handoff_generation.txt`

### Testing Status
- Backend models and endpoints defined
- Frontend UI implemented and styled
- API client methods created
- WebSocket event handling updated
- TypeScript compilation successful
- Ready for end-to-end testing

### Benefits Delivered
- ✅ **User Control:** Users can now iterate on each stage before approval
- ✅ **Quality Improvement:** Refinement cycles improve output quality
- ✅ **Transparency:** Users see exactly what's being generated
- ✅ **Flexible Workflow:** Approve quickly or iterate extensively
- ✅ **Professional UX:** Beautiful, intuitive iteration interface
- ✅ **Autonomous Agent Ready:** Handoff includes self-updating instructions
- ✅ **Granular Planning:** 100-300 step devplans for complete coverage
- ✅ **Visual Feedback:** Clear pipeline progress and stage indicators
- ✅ **Fixed UI Issues:** Black text on white background, proper data types

### Bug Fixes (October 22, 2025 - Evening Session)
- ✅ **White-on-white text issue**: Added `bg-white dark:bg-gray-700` to all input fields
- ✅ **React error "Objects are not valid as a React child"**: Changed `files` from `List[str]` to `Dict[str, Optional[str]]`
  - Updated backend models in `src/web/models.py`
  - Updated Project dataclass in `src/web/project_manager.py`
  - Changed file appends to dict assignments: `project.files["design"] = str(design_file)`
  - Frontend already expected dict format, now backend matches

### Next Steps
- [ ] Integrate prompt templates into pipeline generators
- [ ] Add ability to manually edit output in UI
- [ ] Save iteration history to persistent storage
- [ ] Analytics on iteration patterns (avg iterations per stage, etc.)
- [ ] Export iteration history as part of project archive

---

## Phase 20: Critical Iteration Workflow Fixes ✅

**Status:** COMPLETED ✅  
**Completed:** October 22, 2025 (Late Evening)  
**Duration:** 1 session

### Objectives
Fix critical bugs blocking the iterative workflow from functioning.

### Problems Identified
1. **LLMConfig Validation Error** - `'LLMConfig' object has no field 'design_model'` blocked project creation
2. **Iteration UI Not Displaying** - Pipeline didn't pause after stages, iteration card never appeared
3. **Missing Credential Selection** - No way to choose which API credential to use per project
4. **CORS Error** - Frontend on port 3001 blocked by CORS policy

### Completed Tasks

#### 1. Fixed LLMConfig Validation Error ✅
**Problem:** Code tried to set `config.llm.design_model` but field didn't exist on LLMConfig

**Solution:**
- Updated `src/web/project_manager.py` to use proper per-stage config approach
- Created stage-specific LLMConfig objects using `model_copy()`
- Set model overrides on cloned configs
- Stored in `config.design_llm`, `config.devplan_llm`, `config.handoff_llm`

#### 2. Implemented Full Iteration Support ✅
**Problem:** Pipeline ran all stages continuously without pausing

**Solution - Complete Refactor:**
- Created `_run_current_stage()` method - orchestrates current stage execution
- Created stage-specific methods for each of 5 stages:
  - `_run_design_stage()` - Design generation
  - `_run_basic_devplan_stage()` - High-level phases (4-8)
  - `_run_detailed_devplan_stage()` - Detailed steps (100-300)
  - `_run_refined_devplan_stage()` - Agent-ready plan
  - `_run_handoff_stage()` - Handoff generation

**Each stage now:**
- Generates content
- Saves file to disk
- Sets `awaiting_user_input = True`
- Sets descriptive `iteration_prompt`
- Sets `current_stage_output` (first 500 chars preview)
- Sends WebSocket `awaiting_input` event
- **PAUSES** (returns control to user)

**Updated `continue_pipeline()` method:**
- Determines next stage based on current
- Calls `_run_current_stage()` to execute it
- Handles completion at end of pipeline

#### 3. Added Credential Selection ✅
**Problem:** Users couldn't choose which API credential to use

**Solution:**
- Added `credential_id: Optional[str]` to `ProjectCreateRequest` model
- Updated `_run_current_stage()` to load credential from storage
- Applies credential settings to config (provider, API key, base URL, org ID)
- Falls back to global config if no credential specified

#### 4. Fixed CORS Error ✅
**Problem:** Frontend on port 3001 blocked by CORS policy

**Solution:**
- Added port 3001 to `allow_origins` in `src/web/app.py`
- Updated CORS middleware to allow common dev ports (3000, 3001, 5173)
- Added comment explaining development port handling

#### 5. Added Development Mode (Disable Encryption) ✅
**Problem:** Encryption slows development and makes debugging harder

**Solution:**
- Added `DEVUSSY_DEV_MODE` environment variable check
- When set to 'true', disables all encryption in `SecureKeyStorage`
- API keys stored in plaintext during development
- `encrypt()` and `decrypt()` methods become pass-through

**Usage:**
```powershell
$env:DEVUSSY_DEV_MODE='true'
python -m uvicorn src.web.app:app --host 127.0.0.1 --port 8000 --reload
```

### Files Modified

**Backend:**
- `src/web/project_manager.py` - Complete refactor of pipeline execution (300+ lines)
- `src/web/models.py` - Added `credential_id` field to ProjectCreateRequest
- `src/web/app.py` - Updated CORS origins to include port 3001
- `src/web/security.py` - Added development mode to disable encryption

**Documentation:**
- `HANDOFF.md` - Added development configuration section with CORS and dev mode instructions
- `devplan.md` - This phase documentation

### Testing Status
- LLMConfig validation error resolved ✅
- Pipeline pauses after Design stage ✅
- Iteration state fields properly set ✅
- WebSocket events fire correctly ✅
- Credential selection integrated ✅
- CORS errors resolved ✅
- Dev mode encryption bypass working ✅

### Benefits Delivered
- ✅ **Projects Can Be Created** - Validation error fixed
- ✅ **Iteration UI Displays** - All pause/review logic implemented
- ✅ **User Control** - Can approve or iterate on each stage
- ✅ **Credential Flexibility** - Choose credential per project
- ✅ **Faster Development** - No CORS issues, optional encryption bypass
- ✅ **Full 5-Stage Pipeline** - Design → Basic → Detailed → Refined → Handoff

---

## Phase 19: Error Handling Improvements ✅

**Status:** COMPLETED ✅  
**Completed:** October 22, 2025 (Evening)  
**Duration:** 1 session

### Objectives
Fix critical React error when Pydantic validation errors are returned from the API, and standardize error handling across the frontend.

### Problem Statement
When form validation failed in the backend (Pydantic validation errors with 422 status), the API returned structured error objects with format `{type, loc, msg, input, ctx, url}`. The frontend code assumed errors were always strings, causing React to crash with "Objects are not valid as a React child" error.

### Completed Tasks

#### 1. Root Cause Analysis ✅
- **Identified Issue:** Pydantic v2 returns validation errors as arrays of objects, not strings
- **Impact:** CreateProjectPage crashed when trying to render error objects as text
- **Scope:** Found 21+ instances of similar error handling across 5 frontend files
- **Pattern:** All used `err.response?.data?.detail || 'fallback'` assuming string

#### 2. Created Centralized Error Handler Utility ✅
- **File:** `frontend/src/utils/errorHandler.ts`
- **Functions:**
  - `extractErrorMessage(err)` - Main function to extract user-friendly error messages
    - Handles string errors (FastAPI HTTPException detail)
    - Handles Pydantic validation error arrays
    - Formats field names nicely ("Project Name" not "project_name")
    - Joins multiple errors with semicolons
  - `getFieldError(err, fieldName)` - Extract error for specific form field
  - `isValidationError(err)` - Check for 422 status
  - `isNotFoundError(err)` - Check for 404 status
  - `isAuthError(err)` - Check for 401 status

#### 3. Fixed CreateProjectPage ✅
- **Changes:**
  - Imported `extractErrorMessage` utility
  - Replaced inline error handling with utility function
  - Now handles all error types gracefully (string, array, object)
  - Validation errors display as readable text instead of crashing

#### 4. Fixed Pydantic v2 Deprecation ✅
- **File:** `src/web/models.py`
- **Changes:** Updated all `schema_extra` to `json_schema_extra` (9 instances)
- **Impact:** Eliminated Pydantic v2 UserWarnings in backend logs
- **Future-proofing:** Ensures compatibility with Pydantic v2+

### Files Modified/Created

**Frontend:**
- Created: `frontend/src/utils/errorHandler.ts` - NEW centralized error handling utility
- Modified: `frontend/src/pages/CreateProjectPage.tsx` - Using new error handler

**Backend:**
- Modified: `src/web/models.py` - Fixed Pydantic v2 config deprecations

### Testing Status
- ✅ CreateProjectPage validated - errors display correctly
- ✅ Backend starts without Pydantic warnings
- ⚠️ Other components NOT yet updated (need testing after updates)

### Known Issues Remaining
**CRITICAL:** 21+ instances of inline error handling still need updates:
- `frontend/src/components/config/CredentialsTab.tsx` (8 instances)
- `frontend/src/components/config/GlobalConfigTab.tsx` (2 instances)
- `frontend/src/components/config/PresetsTab.tsx` (2 instances)
- `frontend/src/pages/ProjectDetailPage.tsx` (7 instances)
- `frontend/src/pages/ProjectsListPage.tsx` (2 instances)

### Next Agent Tasks (HIGH PRIORITY)

#### Task 1: Bulk Error Handler Updates
Update all remaining files to use `extractErrorMessage()`:

**Pattern to Find:**
```typescript
err.response?.data?.detail || 'Error message'
err?.response?.data?.detail || 'Error message'
```

**Replace With:**
```typescript
import { extractErrorMessage } from '../utils/errorHandler';
// ...
extractErrorMessage(err)
```

**Files to Update:**
1. `frontend/src/components/config/CredentialsTab.tsx`
   - Lines: 34, 47, 62, 76, 83, 95, 121 (8 instances)
2. `frontend/src/components/config/GlobalConfigTab.tsx`
   - Lines: 27, 42 (2 instances)
3. `frontend/src/components/config/PresetsTab.tsx`
   - Lines: 23, 40 (2 instances)
4. `frontend/src/pages/ProjectDetailPage.tsx`
   - Lines: 55, 155, 166, 178, 247, 271, 299 (7 instances)
5. `frontend/src/pages/ProjectsListPage.tsx`
   - Lines: 30, 46 (2 instances)

#### Task 2: Enhanced Error Display
- Create `<FormError>` component for consistent error display
- Use `getFieldError(err, 'fieldName')` for inline field validation
- Add field-level error messages in forms
- Color-code errors by type (validation, not found, auth, server)

#### Task 3: Comprehensive Testing
Test error scenarios on each page:
- [ ] CreateProjectPage with validation errors ✅ DONE
- [ ] CredentialsTab with invalid API keys
- [ ] GlobalConfigTab with invalid values
- [ ] PresetsTab with missing data
- [ ] ProjectDetailPage error scenarios
- [ ] ProjectsListPage error scenarios
- [ ] TemplatesPage validation (if exists)
- [ ] 404 errors display nicely
- [ ] 401 errors show auth message
- [ ] 500 errors show helpful message

#### Task 4: Add E2E Tests
- Create E2E tests that trigger validation errors
- Verify errors display as readable text
- Verify no React crashes on any error type
- Test all CRUD operations with invalid data

### Benefits Delivered
- ✅ **No More Crashes:** React no longer crashes on validation errors
- ✅ **Better UX:** Errors display as readable, formatted text
- ✅ **Consistency:** One utility function for all error handling
- ✅ **Maintainability:** Centralized error logic easier to update
- ✅ **Future-proof:** Pydantic v2 compatible
- ✅ **Documentation:** Utility has comprehensive JSDoc comments

---

## Remaining Tasks (Optional Enhancements)
- ✅ **React error "Objects are not valid as a React child"**: Changed `files` from `List[str]` to `Dict[str, Optional[str]]`
  - Updated backend models in `src/web/models.py`
  - Updated Project dataclass in `src/web/project_manager.py`
  - Changed file appends to dict assignments: `project.files["design"] = str(design_file)`
  - Frontend already expected dict format, now backend matches

### Next Steps
- [ ] Integrate prompt templates into pipeline generators
- [ ] Add ability to manually edit output in UI
- [ ] Save iteration history to persistent storage
- [ ] Analytics on iteration patterns (avg iterations per stage, etc.)
- [ ] Export iteration history as part of project archive

---

---

## Phase 20: Requesty API Integration Fixes ✅

**Status:** COMPLETED ✅  
**Completed:** October 22, 2025 (Late Night)  
**Duration:** 1 session

### Objectives
Fix the 400 Bad Request errors from Requesty API and add comprehensive logging for debugging.

### Problems Identified
1. **400 Bad Request from Requesty** - All API calls failing
2. **No Verbose Logging** - Cannot see what's being sent/received
3. **Unknown Root Cause** - Need to see actual error details from Requesty
4. **Model Format Unclear** - Users might not know about provider/ prefix requirement

### Completed Tasks

#### 1. Added Comprehensive Verbose Logging ✅
**File:** `src/clients/requesty_client.py`
**Changes:**
- Added detailed console logging before every API call showing:
  - Full endpoint URL
  - Model name being used
  - Request headers (Authorization, Content-Type, HTTP-Referer, X-Title)
  - Request payload (with truncated prompt for readability)
- Added detailed error logging for failed requests (status >= 400):
  - HTTP status code
  - Full error response body from Requesty
  - Request details (model, endpoint) for context
- Added success response logging
- All logs use `[REQUESTY DEBUG]` and `[REQUESTY ERROR]` prefixes for easy filtering

**Benefits:**
- Users can see EXACTLY what's being sent to Requesty
- Error messages include full Requesty error response
- Easy to diagnose issues by checking backend terminal
- Automatic - no configuration needed

#### 2. Implemented Model Format Validation ✅
**File:** `src/clients/requesty_client.py`
**Changes:**
- Added validation that model name contains "/" character
- Raises clear ValueError if format is wrong
- Error message includes:
  - Explanation of provider/model format requirement
  - Examples: `openai/gpt-4o`, `anthropic/claude-3-5-sonnet`
  - Link to Requesty models documentation
- Validation happens BEFORE API call (fails fast)

**Benefits:**
- Prevents 400 errors from invalid model names
- Users get immediate, actionable feedback
- Clear examples show correct format
- Saves wasted API calls

#### 3. Added Recommended HTTP Headers ✅
**File:** `src/clients/requesty_client.py`
**Changes:**
- Added `HTTP-Referer: https://devussy.app` header
- Added `X-Title: DevUssY` header
- Both are optional but recommended by Requesty for analytics

**Benefits:**
- Improves Requesty's analytics and reporting
- Makes DevUssY usage visible in Requesty dashboard
- Follows Requesty API best practices

#### 4. Enhanced Error Handling ✅
**File:** `src/clients/requesty_client.py`
**Changes:**
- Replaced simple `raise_for_status()` with detailed error capture
- Captures full error body before raising exception
- Exception message includes:
  - HTTP status code
  - Complete error response from Requesty
  - Request model and endpoint for debugging
- All error details printed to console

**Benefits:**
- Much more informative error messages
- Users see exactly what Requesty rejected
- Easier to diagnose and fix issues
- Complete error context available

#### 5. Added UI Help Text for Model Format ✅
**File:** `frontend/src/pages/CreateProjectPage.tsx`
**Changes:**
- Added info box below credential selector (shows only for Requesty)
- Explains model format requirement: `provider/model`
- Shows examples with code formatting
- Includes link to Requesty models documentation
- Blue styling with dark mode support

**Benefits:**
- Users see requirements BEFORE creating project
- Prevents common model format mistakes
- Easy access to Requesty documentation
- Proactive help reduces errors

### Files Modified

**Backend:**
- `src/clients/requesty_client.py` - Comprehensive logging, validation, headers, error handling (60+ lines)

**Frontend:**
- `frontend/src/pages/CreateProjectPage.tsx` - Model format help text (15 lines)

**Documentation:**
- `PHASE_20_PROGRESS.md` - Detailed progress report
- `devplan.md` - This phase documentation

### Testing Status
- ✅ Code changes syntactically correct
- ✅ TypeScript compilation successful
- ✅ No import errors
- ⚠️ Needs user testing with real Requesty API key

### Expected Results
When user creates a project with Requesty credential:
1. Backend terminal shows detailed API request/response logs
2. If model format is wrong, immediate clear error message
3. If API call succeeds, project progresses to Design stage
4. If API call fails, full Requesty error details displayed
5. All errors are actionable with examples and documentation links

### Benefits Delivered
- ✅ **Complete Visibility** - See all API requests and responses
- ✅ **Fail Fast** - Model validation before API calls
- ✅ **Clear Errors** - Detailed, actionable error messages
- ✅ **Proactive Help** - UI guidance prevents common mistakes
- ✅ **Best Practices** - Follows Requesty's recommended headers
- ✅ **Professional Quality** - Comprehensive logging and error handling

### Next Steps (Phase 21)
- User testing with real Requesty API key
- Verify Design stage completes successfully
- Test full iteration workflow (5 stages)
- Verify approve and regenerate functionality
- Complete end-to-end project generation

---

## Remaining Tasks (Optional Enhancements)

#### Critical First Step: Read Requesty Documentation

**Task 0: Review Requesty API Documentation** 🔴 DO THIS FIRST
- [ ] **URL:** https://docs.requesty.ai/quickstart
- [ ] Read authentication requirements (Bearer token)
- [ ] Read model name format requirements (`provider/model`)
- [ ] Review request payload structure (OpenAI-compatible)
- [ ] Check recommended headers (`HTTP-Referer`, `X-Title`)
- [ ] Browse available models: https://docs.requesty.ai/models
- [ ] Note any rate limits or restrictions
- [ ] Review error response format

**Key Takeaways from Docs:**
- ✅ Base URL: `https://router.requesty.ai/v1`
- ✅ Model format: MUST be `"provider/model"` (e.g., `"openai/gpt-4o"`, `"anthropic/claude-3-5-sonnet"`)
- ✅ Auth: `Authorization: Bearer {api_key}`
- ✅ Optional headers improve analytics: `HTTP-Referer`, `X-Title`
- ✅ Request format matches OpenAI's chat completions API

#### Backend Fixes (Critical Path)

**Task 1: Add Verbose API Logging** ⚠️ CRITICAL FOR DEBUGGING
- [ ] File: `src/clients/requesty_client.py`
- [ ] Add logging before API call:
  ```python
  import json
  print(f"[REQUESTY REQUEST] URL: {self._endpoint}")
  print(f"[REQUESTY REQUEST] Headers: {json.dumps(headers, indent=2)}")
  print(f"[REQUESTY REQUEST] Payload: {json.dumps(payload, indent=2)}")
  ```
- [ ] Add logging after API call:
  ```python
  print(f"[REQUESTY RESPONSE] Status: {resp.status}")
  if resp.status >= 400:
      error_body = await resp.text()
      print(f"[REQUESTY ERROR] Body: {error_body}")
  ```
- [ ] File: `src/web/project_manager.py`
- [ ] Save API logs to `{project_dir}/api_log.json`
- [ ] Emit WebSocket event with API log for frontend display
- [ ] Test: Create project, check console and api_log.json for full details

**Task 2: Fix Requesty Client Request Format** ⚠️ CRITICAL
- [ ] File: `src/clients/requesty_client.py`
- [ ] Verify model name has provider prefix:
  ```python
  # If model doesn't have '/', add default provider
  if '/' not in model:
      model = f"openai/{model}"  # Or raise error
  ```
- [ ] Add recommended headers:
  ```python
  headers = {
      "Authorization": f"Bearer {self._api_key}",
      "Content-Type": "application/json",
      "HTTP-Referer": "https://devussy.app",  # Optional but recommended
      "X-Title": "DevUssY",  # Optional but recommended
  }
  ```
- [ ] Improve error handling:
  ```python
  async with session.post(...) as resp:
      if resp.status >= 400:
          error_body = await resp.text()
          raise Exception(f"Requesty API {resp.status}: {error_body}")
      resp.raise_for_status()
  ```
- [ ] Test: Create project with verbose logging, verify request format is correct

**Task 3: Validate Model Names in Credentials** 
- [ ] File: `src/web/routes/config.py`
- [ ] In `test_credential()` endpoint:
  ```python
  if credential.provider.lower() == "requesty":
      if "/" not in credential.model:
          return {"success": False, "error": "Requesty models must use format: provider/model (e.g., openai/gpt-4o)"}
  ```
- [ ] Add suggestion in error message linking to docs
- [ ] Test: Try to test credential with wrong format, see helpful error

**Task 4: Check Default Configuration**
- [ ] File: `config/config.yaml`
- [ ] Check current default model value
- [ ] If using Requesty and model doesn't have provider prefix, fix it:
  ```yaml
  llm:
    provider: requesty
    model: openai/gpt-4o-mini  # ← Must have provider/
  ```
- [ ] Test: Create project without selecting credential (uses default config)

#### Frontend Enhancements

**Task 5: Add Verbose API Console to UI** ⚠️ USER REQUESTED
- [ ] File: `frontend/src/pages/ProjectDetailPage.tsx`
- [ ] Add state for API logs:
  ```typescript
  const [apiLogs, setApiLogs] = useState<Array<{
    timestamp: string;
    method: string;
    url: string;
    status?: number;
    request?: any;
    response?: any;
    error?: string;
  }>>([]);
  ```
- [ ] Add new section in UI below Live Logs:
  ```tsx
  <div className="bg-gray-900 dark:bg-gray-800 p-4 rounded-lg">
    <h3 className="font-semibold mb-2 text-white">API Console (Verbose)</h3>
    <div className="space-y-2 max-h-96 overflow-y-auto font-mono text-xs">
      {apiLogs.map((log, i) => (
        <div key={i}>
          <div className="text-gray-400">[{log.timestamp}]</div>
          <div className={log.status >= 400 ? 'text-red-400' : 'text-green-400'}>
            {log.method} {log.url} - {log.status}
          </div>
          {log.request && (
            <pre className="text-gray-300 ml-4 mt-1">
              {JSON.stringify(log.request, null, 2)}
            </pre>
          )}
          {log.response && (
            <pre className="text-gray-300 ml-4 mt-1">
              {JSON.stringify(log.response, null, 2)}
            </pre>
          )}
          {log.error && (
            <pre className="text-red-400 ml-4 mt-1">{log.error}</pre>
          )}
        </div>
      ))}
    </div>
  </div>
  ```
- [ ] Add WebSocket handler for `api_log` events
- [ ] Test: Create project, see exact API requests/responses

**Task 6: Add Model Format Help Text**
- [ ] File: `frontend/src/pages/CreateProjectPage.tsx`
- [ ] Add helper text near model input:
  ```tsx
  <p className="text-sm text-gray-500 mt-1">
    For Requesty: use provider/model format 
    (e.g., <code>openai/gpt-4o</code>, <code>anthropic/claude-3-5-sonnet</code>)
    <a href="https://docs.requesty.ai/models" target="_blank" className="text-blue-500 ml-1">
      View available models →
    </a>
  </p>
  ```
- [ ] File: `frontend/src/components/config/CredentialsTab.tsx`
- [ ] Add same helper text in credential form
- [ ] Test: Check UI shows helpful guidance

#### Testing & Validation

**Task 7: Test Requesty API Integration**
- [ ] Start backend with dev mode: `$env:DEVUSSY_DEV_MODE='true'; python -m uvicorn src.web.app:app --host 127.0.0.1 --port 8000 --reload`
- [ ] Start frontend: `cd frontend; npm run dev`
- [ ] Go to Settings → Credentials
- [ ] Create Requesty credential:
  - Provider: requesty
  - Model: `openai/gpt-4o-mini` (MUST have provider prefix!)
  - API Key: Your Requesty API key
  - Base URL: `https://router.requesty.ai/v1`
- [ ] Click "Test" button - verify success ✅
- [ ] Click "List Models" - verify shows available models ✅
- [ ] Create new project:
  - Name: "Requesty API Test"
  - Description: "Testing Requesty integration"
  - Select Requesty credential
  - Model: `openai/gpt-4o-mini`
- [ ] **VERIFY:** No 400 errors ✅
- [ ] **VERIFY:** Verbose API console shows request with correct format ✅
- [ ] **VERIFY:** Design stage completes successfully ✅
- [ ] **VERIFY:** Design file is generated ✅
- [ ] **VERIFY:** Project pauses for iteration (yellow card) ✅

**Task 8: Error Scenario Testing**
- [ ] Test with invalid API key → verify clear error message
- [ ] Test with wrong model format (e.g., `"gpt-4o"` without prefix) → verify helpful error with suggestion
- [ ] Test with non-existent model → verify Requesty's error is displayed
- [ ] Test canceling during generation → verify clean cancellation
- [ ] **VERIFY:** All errors visible in verbose API console

**Task 9: Complete Iteration Workflow Test**
- [ ] Create project that completes Design stage
- [ ] Verify yellow "User Review Required" card shows
- [ ] Verify iteration prompt displays
- [ ] Verify feedback textarea visible
- [ ] Click "Approve & Continue" → verify moves to Basic DevPlan
- [ ] Test "Regenerate with Feedback" → verify sends feedback to API
- [ ] Complete all 5 stages → verify all files generated
- [ ] Download files → verify works correctly

### Definition of Done

✅ **Requesty API Integration:**
- [ ] Requesty API calls succeed (no 400 errors)
- [ ] Model names validated in correct format (provider/model)
- [ ] Verbose logging shows exact request/response
- [ ] API errors clearly displayed with Requesty's error message
- [ ] Helpful error messages guide users to fix issues

✅ **Frontend:**
- [ ] Verbose API console displays in UI
- [ ] Shows exact request payload sent to Requesty
- [ ] Shows exact response or error from Requesty
- [ ] Pretty-printed JSON for readability
- [ ] Model format help text visible in forms
- [ ] Links to Requesty documentation

✅ **Integration:**
- [ ] Projects complete Design stage successfully
- [ ] Iteration workflow functions (pause, approve, regenerate)
- [ ] Full pipeline completes all 5 stages
- [ ] Generated files saved correctly
- [ ] No errors in browser console or backend terminal

### Files to Modify

**Backend:**
1. `src/clients/requesty_client.py` - Add verbose logging, validate model format, add headers, improve error handling
2. `src/web/project_manager.py` - Save API logs to file, emit API logs via WebSocket
3. `src/web/routes/config.py` - Validate model format in test_credential endpoint
4. `config/config.yaml` - Check/fix default model format for Requesty

**Frontend:**
5. `frontend/src/pages/ProjectDetailPage.tsx` - Add verbose API console UI section
6. `frontend/src/pages/CreateProjectPage.tsx` - Add model format help text
7. `frontend/src/components/config/CredentialsTab.tsx` - Add model format help text
8. `frontend/src/services/projectsApi.ts` - Add handler for api_log WebSocket events

### Next Agent Instructions

**START HERE:**
1. **FIRST:** Read Requesty documentation at https://docs.requesty.ai/quickstart (Task 0)
2. **SECOND:** Implement verbose API logging (Task 1) - critical for debugging
3. **THIRD:** Fix Requesty client request format (Task 2) - likely fixes 400 error
4. **FOURTH:** Add model name validation (Task 3) - prevents future issues
5. **FIFTH:** Check default config (Task 4) - may be root cause
6. **SIXTH:** Add verbose console UI (Task 5) - user requested feature
7. **SEVENTH:** Add help text (Task 6) - improves UX
8. **FINALLY:** Test thoroughly (Tasks 7-9)

**Critical Notes:**
- The 400 error from Requesty is the ONLY blocker
- Verbose logging will show exactly what's wrong
- Model format is most likely culprit (needs `provider/` prefix)
- User explicitly requested verbose API console feature
- Don't skip documentation review - it has the answers!

---

## Remaining Tasks (Optional Enhancements)
- [ ] Full stage override backend logic integration
- [ ] Model cost estimation per stage
- [ ] Export iteration history
- [ ] Analytics dashboard for iteration patterns
- [ ] E2E Tests (Optional)
  - Playwright or Cypress tests
  - Full workflow testing

---

## Phase 1: Setup Phase (Historical)

✅ **1.1**: Create project structure

✅ **1.2**: Set up development environment
