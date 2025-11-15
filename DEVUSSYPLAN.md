# DEVUSSYPLAN

**Repository**: https://github.com/mojomast/devussy-testing  
**Version**: 0.2.0 (Release 01)  
**Status**: Phases 1-5 Complete (45% of roadmap)  
**Tests**: 63 passing (56 unit + 7 integration)

## High-Level Goals

- **Interview existing projects** and generate context-aware devplans.
- **Stream 5 phases in the terminal** (`plan`, `design`, `implement`, `test`, `review`) with real-time token output.
- **Support steering**: cancel a phase, collect feedback, regenerate with context while other phases continue.
- **Ship a polished CLI experience**: `devussy interview` and `devussy generate-terminal`, with help, docs, and tests.

---

## Architecture Snapshot (from devussy-complete-plan)

- **CLI**
  - `devussy interview [directory] [--output]`
  - `devussy generate-terminal <devplan>`
- **Interview layer**
  - `RepositoryAnalyzer`
  - `CodeSampleExtractor`
  - `InterviewEngine`
  - `ExistingProjectDevPlanGenerator`
  - `InterviewHandoffBuilder`
- **Terminal layer**
  - `TerminalStreamer` (grid UI)
  - `TerminalStreamerWithSteering`
  - `PhaseStateManager`
  - `Fullscreen Viewer`
  - `SteeringOrchestrator`
- **Phase generation**
  - `TerminalPhaseGenerator` (streaming + steering)
- **Support**
  - `help.ts`, tests, integration tests

---

## Implementation Phases & Tasks

### Phase 1 – Repository Analysis Engine ✅ COMPLETE

**Outcome:** Given a project directory, produce a `RepoAnalysis` object (type, structure, dependencies, metrics, patterns, config).

**Status:** Fully implemented and tested. All 15 unit tests and 7 integration tests passing.

**Completed Tasks**

- **Scaffold types & core class**
  - [x] Created `src/interview/repository_analyzer.py` (Python implementation).
  - [x] Defined `RepoAnalysis`, `DirectoryStructure`, `DependencyInfo`, `CodeMetrics`, `CodePatterns`, `ConfigFiles` dataclasses.
  - [x] Implemented `RepositoryAnalyzer` constructor accepting `root_path`.

- **Implement detection routines**
  - [x] `detect_project_type()` – detects Python, Node, Go, Rust, Java projects via manifest files.
  - [x] `analyze_structure()` – directory walk, classifies folders (`src`, `tests`, `config`, CI dirs).
  - [x] `analyze_dependencies()` – parses deps for Node, Python, Go, Rust, Java.
  - [x] `analyze_code_metrics()` – total file/line counts (per-language breakdown pending).
  - [x] `detect_patterns()` – infers test frameworks (pytest, jest) and build tools.
  - [x] `extract_config_files()` – gathers key config files (CI, build, tooling).

- **Pipeline integration**
  - [x] Added `RepoAnalysis.to_prompt_context()` method for LLM-friendly JSON representation.
  - [x] Threaded `repo_analysis` through entire pipeline (`BasicDevPlanGenerator`, `DetailedDevPlanGenerator`, `HandoffPromptGenerator`).
  - [x] Updated Jinja templates to include repo context sections when available.
  - [x] Wired into LLM-driven interview flow via `interactive_design --llm-interview --repo-dir`.

- **CLI exposure**
  - [x] Added `devussy interview [directory]` command with full LLM config options.
  - [x] Added `devussy analyze-repo` command with JSON output for debugging.

- **Tests**
  - [x] Added `tests/unit/test_repository_analyzer.py` with 15 passing tests.
  - [x] Added `tests/integration/test_repo_aware_pipeline.py` with 7 passing tests.
  - [x] Test coverage includes all supported project types and edge cases.

**Definition of Done** ✅

- [x] Running analyzer on sample repos yields structured `RepoAnalysis`.
- [x] Handles malformed/mixed projects without crashing.
- [x] Tests green for all supported project types.
- [x] No diagnostics or syntax errors.

**Known Limitations (Technical Debt)**

- Metrics remain coarse (total counts only; no per-language file counts or complexity hints).
- Error handling for malformed repos is best-effort (errors collected but not richly surfaced).
- GPT-5 mini requires higher token limits (2000+) due to reasoning token usage.

---

### Phase 2 – Interview Engine ✅ COMPLETE

**Outcome:** LLM-driven interactive interview that uses the analysis to generate context-aware devplans.

**Status:** Fully implemented with LLM-driven interview, code sample extraction, and project summary display. All tests passing. Real-world validation completed.

**Completed Tasks**

- **LLM-driven interview**
  - [x] Implemented `LLMInterviewManager` in `src/llm_interview.py`.
  - [x] Wired to accept `RepoAnalysis` for context-aware questioning.
  - [x] Integrated with `interactive_design --llm-interview --repo-dir` flow.
  - [x] CLI command `devussy interview` fully functional.

- **Code sample extraction**
  - [x] Created `src/interview/code_sample_extractor.py`.
  - [x] Implemented `CodeSampleExtractor.extract_samples(selected_parts, analysis)` to pull:
    - [x] Architecture samples (key files that show project structure)
    - [x] Pattern examples (representative code showing conventions)
    - [x] Relevant files based on user's stated goals
    - [x] Representative test files
  - [x] Added 15 comprehensive tests for sample extraction logic.
  - [x] All tests passing (15/15 unit tests).
  - [x] Wired into interview flow via `to_generate_design_inputs()`.
  - [x] Code samples passed through entire pipeline to all generators.

- **Enhanced interview UX**
  - [x] Added `_print_project_summary()` to show analysis summary before interview starts.
  - [x] Project summary displays formatted repo context (type, structure, deps, metrics).
  - [x] Code sample extraction integrated into interview manager.
  - [x] `extract_code_samples()` and `get_code_samples_context()` methods implemented.

- **Real-world validation**
  - [x] Created `scripts/test_interview_validation.py` for automated testing.
  - [x] Validated repository analysis on devussy project itself (481 files, 52k lines).
  - [x] Verified code sample extraction (5 samples with architecture and patterns).
  - [x] Confirmed interview manager initialization with repo context.
  - [x] Validated design inputs include code samples (10k+ characters).
  - [x] All validation tests passing with real Requesty API.

**Definition of Done** ✅

- [x] Interview yields context-aware devplan output.
- [x] Code samples extracted and included in prompts.
- [x] User experience is polished and conversational.
- [x] Real-world testing validates prompt quality.
- [x] Project summary displays before interview starts.
- [x] Code samples flow through entire pipeline.

---

### Phase 3 – Context-Aware DevPlan Generation ✅ COMPLETE

**Outcome:** Given analysis, interview answers, and code samples, generate a devplan JSON ready for the terminal UI.

**Status:** Fully implemented and integrated into pipeline. All tests passing.

**Completed Tasks**

- **Devplan generator**
  - [x] Integrated repo context into existing `BasicDevPlanGenerator` and `DetailedDevPlanGenerator`.
  - [x] `PipelineOrchestrator` accepts and passes `repo_analysis` through all stages.
  - [x] Context prompt assembly includes:
    - [x] Repo summary (project type, structure, dependencies)
    - [x] Interview answers (via `LLMInterviewManager`)
    - [x] Constraints and timeline (from user inputs)

- **LLM integration**
  - [x] Uses existing `LLMClient` abstraction with provider-agnostic interface.
  - [x] `DevPlan` schema already defined with phases, tasks, notes, risks.
  - [x] Supports all configured providers (OpenAI, Aether, AgentRouter, Requesty, Generic).

- **Handoff builder**
  - [x] Integrated into `HandoffPromptGenerator` in `src/pipeline/handoff_prompt.py`.
  - [x] Template `templates/handoff_prompt.jinja` includes repo context sections.
  - [x] Embeds analysis, devplan summary, and instructions for downstream use.

- **Tests**
  - [x] `tests/integration/test_repo_aware_pipeline.py` validates:
    - [x] Repo context threaded through all pipeline stages.
    - [x] Templates include repo context when available.
    - [x] Backward compatibility (works without repo_analysis).
    - [x] Real repository analysis with Python, Node, mixed projects.

**Definition of Done** ✅

- [x] `devussy interview` produces context-aware devplan output.
- [x] Handoff prompt includes repo context and is usable by phase generators.
- [x] All integration tests passing.

**Pending Enhancement**

- [x] Code sample extraction (completed in Phase 2).
- [x] Real-world LLM validation with actual API calls (completed - GPT-5 mini via Requesty working).

---

### Phase 4 – Terminal UI Core ✅ FOUNDATION COMPLETE

**Outcome:** Textual-based terminal grid with 5 phase boxes, basic interactions, and status updates.

**Status:** Foundation complete with Textual library, phase state management, and responsive grid layout. Basic proof-of-concept working. Ready for Phase 5 token streaming integration.

**Completed Tasks**

- **Library decision**
  - [x] Researched Python terminal UI libraries (Rich, Textual, urwid, blessed, py-cui).
  - [x] Created `docs/terminal-ui-library-decision.md` with analysis and rationale.
  - [x] Selected Textual as the framework (async-first, grid layouts, Rich integration).
  - [x] Added `textual>=0.47.0` to requirements.txt.

- **Phase state management**
  - [x] Created `src/terminal/phase_state.py` with `PhaseStreamState` and `PhaseStateManager`.
  - [x] Implemented all state management methods:
    - [x] `initialize_phase` - Start phase generation
    - [x] `get_state` - Retrieve phase state
    - [x] `update_status` - Change phase status
    - [x] `append_content` - Stream tokens
    - [x] `capture_generation_context` - Save context for regeneration
    - [x] `record_cancellation` - Handle cancellation
    - [x] `record_steering_answers` - Store feedback
    - [x] `reset_for_regeneration` - Prepare for regeneration
    - [x] `record_error` - Handle errors
    - [x] `is_complete` - Check if all phases done
  - [x] Added 14 comprehensive unit tests (all passing).

- **Core UI**
  - [x] Created `src/terminal/terminal_ui.py` with Textual app.
  - [x] Implemented `PhaseBox` widget with:
    - [x] Status badge display (⏸ Idle, ▶ Streaming, ✓ Complete, etc.)
    - [x] Color-coded borders (idle/streaming/complete/interrupted/error/regenerating)
    - [x] Scrollable content area
    - [x] Reactive updates from state manager
  - [x] Implemented `DevussyTerminalUI` main app with:
    - [x] Responsive grid layout (5 cols / 3x2 / 1x5 based on terminal width)
    - [x] Header and footer with keybindings
    - [x] Phase box management and updates
  - [x] Basic keybindings: q=Quit, ?=Help, c=Cancel, f=Fullscreen

- **Demo and testing**
  - [x] Created `scripts/demo_terminal_ui.py` for visual testing.
  - [x] Simulates streaming generation with fake tokens.
  - [x] Tests responsive layout at different terminal widths.
  - [x] Demo works and displays all phase states correctly.
  - [x] Added per-phase token count badges and grid truncation (last 40 lines) for readability.

**Pending Tasks (Phase 4 Enhancements)**

- **Rendering enhancements**
  - [ ] Improve status badge styling and animations.

- **Keyboard / mouse**
  - [x] Implement focus movement between phases (arrow keys, tab).
  - [x] Add mouse click to focus/select phases.
  - [ ] Implement dedicated help overlay/screen (? key) with full keybinding list.

**Definition of Done** ✅

- [x] Phase state manager fully implemented and tested.
- [x] Basic grid layout adapts to terminal width.
- [x] Phase boxes display status and content.
- [x] Dummy phase generator can push text into boxes (demo works).
- [x] Layout tested at multiple terminal widths.
- [x] All 51 tests passing (44 unit + 7 integration).

---

### Phase 5 – Token Streaming ✅ COMPLETE

**Outcome:** Stream LLM tokens into phase boxes with cancellation support.

**Status:** Fully implemented and tested. All 12 unit tests passing.

**Completed Tasks**

- **Phase generator**
  - [x] Created `src/terminal/phase_generator.py` with `TerminalPhaseGenerator` class.
  - [x] Implemented `generate_phase_streaming(phase_name, devplan, on_token, **kwargs)`:
    - [x] Builds phase-specific prompt from devplan structure.
    - [x] Calls streaming LLM API via `llm_client.generate_completion_streaming`.
    - [x] On each token: appends to state manager and calls optional callback.
    - [x] Respects abort event for cancellation and records context via `PhaseStateManager`.
  - [x] Implemented `cancel_phase(phase_name)` to abort streaming generation.
  - [x] Implemented `regenerate_phase_with_steering(phase_name, devplan, steering_feedback)` for steering workflow.
  - [x] Implemented `generate_all_phases(devplan, phase_names, on_token)` for concurrent generation.

- **Terminal UI integration**
  - [x] Updated `DevussyTerminalUI` to accept `phase_generator` and `devplan` parameters.
  - [x] Added async task management for concurrent phase generation.
  - [x] Implemented periodic UI update loop (100ms interval).
  - [x] Wired cancel keybinding ('c') to phase generator cancellation.
  - [x] Added automatic generation start on mount when configured.

- **Testing**
  - [x] Created `tests/unit/test_phase_generator.py` with 12 comprehensive tests:
    - [x] Prompt building (basic, with steering, unknown phase)
    - [x] Streaming generation (success, with callback, cancellation, error)
    - [x] Regeneration with steering feedback
    - [x] Concurrent generation of all phases
  - [x] Created `scripts/test_streaming_integration.py` for end-to-end validation:
    - [x] Console streaming test (without UI)
    - [x] Phase cancellation test
    - [x] Interactive terminal UI test (with real LLM)

- **Module exports**
  - [x] Updated `src/terminal/__init__.py` to export `TerminalPhaseGenerator`.

**Definition of Done** ✅

- [x] Real streaming from LLM to terminal boxes.
- [x] Cancellation aborts stream and stores enough context to regenerate.
- [x] All 26 tests passing (12 phase generator + 14 phase state manager).
- [x] Integration test script validates end-to-end flow.
- [x] No diagnostics or syntax errors.

---

### Phase 6 – Fullscreen Viewer (Day 9)

**Outcome:** Click/focus a phase to see full content with scrolling and character count.

**Tasks**

- [ ] Create `src/terminal/fullscreen-viewer.ts` (or equivalent integration).
- [ ] Implement `showFullscreenPhase(phaseName)`:
  - [ ] Hide grid boxes.
  - [ ] Create fullscreen box with header, scrollable content, footer with char count.
- [ ] Implement keybindings:
  - [ ] `j` / `k` and arrow keys for scrolling.
  - [ ] `ESC` to return to grid.

**Definition of Done**

- [ ] User can open fullscreen for any phase, scroll content, and return without losing state.

---

### Phase 7 – Steering Workflow (Days 10–11)

**Outcome:** Press `C` on a streaming phase → cancel, open steering overlay, regenerate with feedback while other phases continue.

**Tasks**

- **Steering UI**
  - [ ] Create `src/terminal/steering-interview.ts`.
  - [ ] Implement `showSteeringInterview(phaseName)` overlay:
    - [ ] Partial output preview.
    - [ ] 3 text fields: issue, desired change, constraints.
    - [ ] Buttons/keys: Regenerate, Cancel.

- **Cancel handler**
  - [ ] Implement `handlePhaseCancel(phaseName)`:
    - [ ] Abort controller signal for that phase.
    - [ ] Update phase status to `interrupted`.
    - [ ] Invoke steering overlay.

- **Steering orchestrator**
  - [ ] Create `src/terminal/steering-orchestrator.ts`.
  - [ ] Implement `steerPhase(phaseName, devplan)`:
    - [ ] Record steering answers.
    - [ ] Close overlay.
    - [ ] Call `regeneratePhase(phaseName, devplan)`.

- **Steering-aware phase generator**
  - [ ] Extend `TerminalPhaseGenerator` with `regeneratePhaseWithSteering` and `buildSteeringPrompt`.
  - [ ] Regenerate using original prompt, partial output, and steering answers.

**Definition of Done**

- [ ] User can cancel a phase mid-generation, give feedback, and see a new generation that incorporates feedback.
- [ ] Other phases continue streaming uninterrupted.

---

### Phase 8 – CLI Integration (Day 12)

**Outcome:** `devussy interview` and `devussy generate-terminal` wired end-to-end.

**Tasks**

- [ ] Create `src/cli/commands/interview.ts`:
  - [ ] Args: `[directory]` (default `.`), `--output <path>`.
  - [ ] Run analyzer → summary → interview.
  - [ ] Run code sample extractor + devplan generator, save `devplan-interview.json`.
  - [ ] Optionally launch terminal generation via `GenerationOrchestrator`.

- [ ] Create `src/cli/commands/generate-terminal.ts`:
  - [ ] Arg: `<devplan>`.
  - [ ] Load JSON, instantiate `GenerationOrchestrator`, call `start()`.

- [ ] Create `src/terminal/generation-orchestrator.ts` tying together `PhaseStateManager`, `TerminalPhaseGenerator`, `TerminalStreamerWithSteering`.

**Definition of Done**

- [ ] `devussy interview` works from a real repo and produces a usable devplan.
- [ ] `devussy generate-terminal devplan-interview.json` launches grid UI and streams phases.

---

### Phase 9 – TerminalStreamerWithSteering Integration (Day 13)

**Outcome:** Unified terminal UI with streaming, fullscreen, and steering all working together.

**Tasks**

- [ ] Create `src/terminal/terminal-streamer-steering.ts` extending `TerminalStreamer`.
- [ ] Implement `generateAllPhases(devplan)`:
  - [ ] Kick off concurrent streaming for `plan`, `design`, `implement`, `test`, `review` with individual `AbortController`s.
- [ ] Wire cancel handling, steering overlay, regeneration, and UI updates.
- [ ] Ensure correct state transitions across idle/streaming/interrupted/steering/regenerating/complete/error.

**Definition of Done**

- [ ] End-to-end flow: devplan → grid streaming → cancel → steering → regeneration → completion of all phases.

---

### Phase 10 – Testing & Polish (Day 14)

**Outcome:** Strong test coverage and resilience.

**Tasks**

- [ ] Implement tests:
  - [ ] `tests/interview/repository-analyzer.test.ts`
  - [ ] `tests/interview/interview-engine.test.ts`
  - [ ] `tests/interview/devplan-generator.test.ts`
  - [ ] `tests/terminal/terminal-streamer.test.ts`
  - [ ] `tests/terminal/steering-orchestrator.test.ts`
  - [ ] `tests/terminal/fullscreen-viewer.test.ts`
  - [ ] `tests/integration/full-workflow.test.ts`
- [ ] Run tests against real and synthetic projects.
- [ ] Tighten error handling and performance (e.g., debounced rendering).

**Definition of Done**

- [ ] ~80%+ coverage.
- [ ] Integration tests for interview → generation and cancel → steer → regenerate flows passing.

---

### Phase 11 – Documentation & Help (Day 15)

**Outcome:** Users can discover and effectively use the terminal UI.

**Tasks**

- [ ] Implement `src/terminal/help.ts` with in-app help content and keyboard shortcuts.
- [ ] Wire `?` key to open/close help.
- [ ] Update CLI help (descriptions/options).
- [ ] Extend top-level docs (README, splash screen docs) explaining:
  - [ ] Interview mode.
  - [ ] Streaming UI and phases.
  - [ ] Steering workflow.
  - [ ] Troubleshooting & common errors.

**Definition of Done**

- [ ] Users can run `devussy interview` and `devussy generate-terminal` and understand the flow without reading source.

---

## Success Criteria Checklist

- **Interview Mode**
  - [ ] Analyzes arbitrary project directory.
  - [ ] Detects project type, dependencies, and patterns.
  - [ ] 7-question interview feels natural.
  - [ ] Generated devplans fit into existing codebases.
  - [ ] Works for Node, Python, Go, Rust, Java.

- **Terminal Streaming UI**
  - [ ] 5 phases stream in parallel.
  - [ ] Real-time status updates and color-coded borders.
  - [ ] Responsive layout (5 cols / 2x3 / vertical).
  - [ ] No noticeable performance lag.

- **Fullscreen Viewer**
  - [ ] Click/focus to fullscreen any phase.
  - [ ] Vim/arrow keys for scrolling.
  - [ ] Character count visible.
  - [ ] ESC returns to grid.

- **Steering Workflow**
  - [ ] Press `C` cancels mid-generation.
  - [ ] Steering overlay shows partial output.
  - [ ] 3 feedback questions collected.
  - [ ] Other phases keep streaming.
  - [ ] Regenerated output replaces cancelled content.
  - [ ] Regeneration uses original prompt + API request + feedback.

- **Integration & DX**
  - [ ] `devussy interview` is end-to-end usable.
  - [ ] `devussy generate-terminal` works with interview output.
  - [ ] Help + keyboard shortcuts documented.
  - [ ] Errors are surfaced clearly.

---

## Repository Status (Session 5)

**Repository Created**: ✅ https://github.com/mojomast/devussy-testing

**Release 01 Details**:
- **Commit**: 809b6ed (initial commit with clean history)
- **Files**: 146 files, 34,793 lines
- **Status**: Live and accessible
- **Tests**: All 63 tests passing
- **Documentation**: Complete (README, session summaries, handoff docs)

**What's Included**:
- ✅ Phase 1-3: Interview Mode (repository analysis, LLM interview, code extraction)
- ✅ Phase 4: Terminal UI Foundation (Textual-based TUI, phase state management)
- ✅ Phase 5: Token Streaming (real-time LLM streaming, cancellation, concurrent generation)
- ✅ Comprehensive test suite (56 unit + 7 integration)
- ✅ Complete documentation and setup scripts

**Git History**:
- Clean repository created from fresh export
- Bypassed corruption in original repository
- Single initial commit with all Release 01 code
- Ready for continued development

**Next Steps**:
1. Clone: `git clone https://github.com/mojomast/devussy-testing.git`
2. Install: `pip install -e .`
3. Test: `pytest -q`
4. Continue with Phase 6 (Fullscreen Viewer)

---

**Note:** For the circular development handoff prompt, see `devussyhandoff.md`.
