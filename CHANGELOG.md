# Changelog

All notable changes to Devussy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.2] - 2025-11-27

### ✨ Added - Inline Design Refinement
- **New InlineRefinementPanel Component** (`components/pipeline/InlineRefinementPanel.tsx`)
  - Embedded chat interface for design refinement directly below Complexity Assessment
  - Replaces the separate floating window approach with inline UX
  - Supports `/analyze` command for automated design review
  - Supports `/apply` command to finalize and continue
  - "Apply & Continue" button triggers complexity re-analysis

- **Improved Adaptive Pipeline Integration**
  - "Refine Design" button now toggles inline panel instead of spawning separate window
  - After refinement completes, automatically re-runs complexity analysis
  - Better visual flow: Complexity → Inline Refinement → Validation → Correction
  - Refinement panel positioned contextually below Complexity Factors

### 🔧 Changed
- **DesignView.tsx**: Added `showInlineRefinement` state and integrated `InlineRefinementPanel`
- Refine Design button now shows "Hide Refinement" when panel is open
- `onRequestReanalysis` callback wired to re-trigger `analyzeComplexity()`

## [0.4.1] - 2025-11-27

### ✨ Added - Per-Stage Model Configuration
- **Extended LLM Configuration**: Added per-stage model configuration for all pipeline phases
  - `interview_llm` - Project discovery conversation stage
  - `complexity_llm` - Complexity analysis stage
  - `validation_llm` - Design validation stage
  - `correction_llm` - Correction loop stage
  - `execute_llm` - Phase execution stage
  - Updated `get_llm_config_for_stage()` to support all stages including `plan` alias
  - Environment variable support for per-stage API keys

### 📥 Added - Download Buttons for All Pipeline Elements
- **New DownloadButton Component** (`components/ui/DownloadButton.tsx`)
  - Reusable download button for markdown file exports
  - Helper functions for formatting different content types

- **Download Buttons Added to All Pipeline Stages**:
  - **InterviewView**: Download interview transcript as markdown
  - **DesignView**: Download generated design document
  - **ComplexityAssessment**: Download complexity analysis report
  - **ValidationReport**: Download validation results with sanity review
  - **CorrectionTimeline**: Download correction loop history
  - **PlanView**: Download development plan
  - **ExecutionView**: Download all phase execution results
  - **HandoffView**: Individual download buttons for each tab (handoff, design, plan, phases)

### 📚 Configuration
- Updated `config/config.yaml` with documentation for all per-stage LLM settings
- Extended `src/config.py` with full per-stage configuration loading

## [0.4.0] - 2025-11-27

### 🎨 Added - UI/UX Improvements
- **Redesigned New Project Window**: Compact, space-efficient layout with ~30% smaller footprint
  - Grouped sections with clear headers and icons (Quick Start, Guided Setup, Manual Configuration, Options)
  - Blue gradient header matching design system
  - Scrollable content area with fixed header and footer
  - Reduced window size from 800x750 to 550x650 pixels
  
- **Full Theme Support**: Three beautiful themes for personalized experience
  - **Bliss Theme**: Windows XP-style with clean white/gray/blue aesthetic
  - **Terminal Theme**: Matrix-style hacker aesthetic with green-on-black colors
  - **Default Theme**: Adaptive light/dark mode using CSS variables
  
- **Theme-Aware ModelSettings Component**
  - All UI elements (buttons, inputs, tabs, borders) now respect theme selection
  - Dropdown and window modes both fully themed
  - Consistent visual language across all three themes
  - Proper color adaptation for backgrounds, text, accents, and hover states

### ✨ Enhanced
- Better space utilization throughout the application
- Improved visual hierarchy with organized, bordered sections
- Theme toggle easily accessible in taskbar (or Start Menu in Bliss theme)
- Cohesive design language across all windows and components
- More intuitive form layout in new project window

### 🐛 Fixed - Docker Deployment
- Added proper `NEXT_PUBLIC_*` environment variable handling in Docker
- Build args now have sensible defaults for production deployment
- Frontend Dockerfile properly passes environment variables to both build and runtime
- docker-compose.prod.yml includes all necessary environment variables and build args
- Added `.env.example` for easier deployment configuration

### 📚 Documentation
- Updated README.md with v0.4.0 feature highlights
- Updated devussy-web README.md with new features and version
- Enhanced in-app help with v0.4.0 changelog section
- Added visual examples and descriptions of new themes
- Bumped version to 0.4.0 in package.json

## [0.3.0] - 2025-11

### Added
- Initial adaptive LLM pipeline implementation
- Complexity analysis and validation
- Multi-phase concurrent execution
- HiveMind multi-agent swarm generation
- IRC chat integration
- Checkpoint system for resumable pipelines
- Web UI with Next.js 15
- Real-time streaming via Server-Sent Events (SSE)
- Window management system with draggable windows
- Per-stage model configuration

### Features
- Interactive interview phase
- Design generation with validation
- Development plan with editable phase cards
- Concurrent phase execution with live streaming
- Complete artifact download with phase documents
- Taskbar and window management

## [0.2.0] - 2025-10

### Added
- Core CLI implementation
- Basic pipeline stages
- Template system with Jinja2
- Multiple LLM provider support (OpenAI, Requesty, Aether, AgentRouter)

## [0.1.0] - 2025-09

### Added
- Initial project structure
- Basic concept and methodology documentation
- Circular development workflow
- Anchor-based context management (AGENTS.md)

---

[0.4.1]: https://github.com/mojomast/devussy/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/mojomast/devussy/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/mojomast/devussy/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/mojomast/devussy/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/mojomast/devussy/releases/tag/v0.1.0
