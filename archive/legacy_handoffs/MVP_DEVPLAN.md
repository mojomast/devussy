# MVP Development Plan: Interactive DevPlan Builder

## 🎯 MVP Goal
Build an **interactive DevPlan building system** that asks the right questions and generates aligned devplans and handoff prompts through both **CLI and Web interfaces**.

---

## Current State Assessment

### ✅ What Works
- **Core pipeline**: Project Design → DevPlan → Handoff generation
- **CLI commands**: All 9 commands functional (generate-design, generate-devplan, etc.)
- **Multiple LLM providers**: OpenAI, Generic, Requesty
- **Package built**: Ready for distribution (v0.1.0)
- **227/242 tests passing** (93.8%)

### ❌ What's Missing for MVP
1. **Interactive questioning system** - Currently requires all inputs upfront via flags
2. **Web interface** - No FastAPI/web UI exists yet
3. **Smart question flow** - Tool doesn't guide users through what to provide
4. **DevPlan/Handoff alignment** - Generated docs don't reflect interactive approach

---

## Phase 1: Interactive CLI Questionnaire ⏳ (3-5 days)

**Goal**: Transform CLI from "all flags upfront" to "guided conversation"

### 1.1: Design Interactive Question Flow
- Map out the question tree (project type → languages → frameworks → etc.)
- Define conditional questions based on previous answers
- Create question categories: Essential, Recommended, Advanced
- Document the flow in `docs/INTERACTIVE_FLOW.md`

### 1.2: Create Interactive Input Module
- Build `src/interactive.py` with `InteractiveQuestionnairemanager`
- Implement question types: text, choice, multi-choice, yes/no
- Add validation for each question type
- Support skipping optional questions
- Allow going back to previous questions

### 1.3: Implement Rich CLI Interactions
- Use `rich` library for beautiful CLI prompts (already a dependency)
- Add progress indicators showing "Question 3 of 10"
- Display helpful examples for each question
- Show context: "Based on your choice of Python, we recommend..."
- Add "Why are we asking this?" help text

### 1.4: Update CLI Commands for Interactive Mode
- Add `--interactive` / `-i` flag to `generate-design` command
- Default to interactive mode if no flags provided
- Keep flag-based mode for automation/CI
- Add `devussy interactive-design` dedicated command
- Update help text and examples

### 1.5: Save and Resume Sessions
- Save partial responses to `.devussy_session/current_session.json`
- Add `devussy resume-session` command
- Support `--from-session` flag to continue where you left off
- Allow editing previous answers

### 1.6: Testing Interactive Features
- Create `tests/unit/test_interactive.py`
- Mock user input for automated testing
- Test all question types and validations
- Test session save/resume functionality
- Add integration tests for full interactive flow

---

## Phase 2: Web Interface Foundation 🌐 (5-7 days)

**Goal**: Build FastAPI-based web UI for interactive devplan building

### 2.1: FastAPI Setup
- Create `src/api/` directory structure
- Build `src/api/app.py` with FastAPI application
- Set up CORS, middleware, error handlers
- Add health check endpoint
- Configure uvicorn for development

### 2.2: Question API Endpoints
- `GET /api/questions/start` - Get first question
- `POST /api/questions/{id}/answer` - Submit answer, get next question
- `GET /api/session/{id}` - Get current session state
- `PATCH /api/session/{id}/answer/{qid}` - Edit previous answer
- `DELETE /api/session/{id}` - Clear session

### 2.3: WebSocket for Real-time Streaming
- Implement WebSocket endpoint `/ws/generate`
- Stream LLM responses in real-time as they're generated
- Send progress updates during generation
- Handle connection drops gracefully
- Add reconnection logic on client side

### 2.4: Simple Web UI
- Create `src/api/static/` for HTML/CSS/JS
- Build single-page app with vanilla JS (or React if time allows)
- Implement question-by-question form UI
- Add progress bar showing completion percentage
- Display real-time LLM streaming output
- Show generated devplan/handoff in preview panel

### 2.5: API Authentication (Optional but Recommended)
- Add API key authentication
- Create `src/api/auth.py` with key validation
- Store API keys in config/environment
- Add rate limiting per API key
- Document authentication in `docs/API.md`

### 2.6: API Documentation
- Auto-generate OpenAPI/Swagger docs
- Add detailed endpoint descriptions
- Include request/response examples
- Document WebSocket protocol
- Create Postman collection

### 2.7: API Testing
- Create `tests/api/` directory
- Test all REST endpoints with pytest
- Test WebSocket connections
- Test authentication and rate limiting
- Integration tests for full API workflows

---

## Phase 3: Align Templates & Generated Docs 📝 (2-3 days)

**Goal**: Update DevPlan and Handoff templates to reflect interactive approach

### 3.1: Update Project Design Template
- Add section documenting user's interactive responses
- Include question-answer pairs in design doc
- Show which questions were asked and why
- Add metadata about interactive session

### 3.2: Update DevPlan Template
- Emphasize interactive user experience in plan
- Include steps for implementing interactive features
- Add phases for web interface development
- Align with actual MVP goals

### 3.3: Update Handoff Template
- Focus on interactive features in handoff
- Describe the question flow architecture
- Document web API endpoints
- Provide context for next agent about UI/UX decisions

### 3.4: Create Interactive-Specific Templates
- `templates/interactive_session_report.jinja` - Session summary
- `templates/question_validation_report.jinja` - Validation rules doc
- `templates/api_documentation.jinja` - Auto-generated API docs

---

## Phase 4: Enhanced Question Intelligence 🧠 (3-4 days)

**Goal**: Make questions smart, contextual, and adaptive

### 4.1: Context-Aware Question Engine
- Questions adapt based on previous answers
- "You selected FastAPI, we recommend PostgreSQL or MongoDB for databases"
- Skip irrelevant questions based on context
- Provide examples relevant to user's tech stack

### 4.2: LLM-Powered Question Suggestions
- Use LLM to suggest additional questions based on project type
- Generate custom questions for unique scenarios
- Ask clarifying questions when requirements are vague
- Offer "Let me think about this" option to gather more context

### 4.3: Validation & Quality Checks
- Validate responses against known patterns
- Warn about potential issues: "Python + .NET is unusual, did you mean..."
- Suggest alternatives: "Consider using TypeScript instead of JavaScript for large projects"
- Check for common mistakes

### 4.4: Question Library & Presets
- Create `config/question_presets.yaml` with common flows
- Presets: "Web App", "API Service", "CLI Tool", "Data Pipeline", etc.
- Allow users to select preset and customize
- Community-contributed question flows

---

## Phase 5: Documentation & Examples 📚 (1-2 days)

**Goal**: Comprehensive docs for interactive system

### 5.1: User Documentation
- Update `README.md` with interactive examples
- Create `docs/INTERACTIVE_GUIDE.md` - Step-by-step tutorial
- Add screenshots/GIFs of CLI and web interface
- Document keyboard shortcuts and navigation

### 5.2: Developer Documentation
- Document question engine architecture in `docs/ARCHITECTURE.md`
- API integration examples in `docs/EXAMPLES.md`
- Contribution guide for adding new questions
- WebSocket protocol specification

### 5.3: Video Tutorials (Optional)
- Record CLI interactive session demo
- Record web interface walkthrough
- Create YouTube playlist
- Embed in README

---

## Phase 6: Testing & Polish ✨ (2-3 days)

**Goal**: Production-ready quality

### 6.1: Comprehensive Testing
- Achieve 80%+ test coverage for new code
- End-to-end tests for interactive flows
- Load testing for web API
- Cross-platform testing (Windows, Mac, Linux)

### 6.2: Performance Optimization
- Optimize question rendering speed
- Cache LLM responses where appropriate
- Minimize API calls during interactive session
- Async improvements for web interface

### 6.3: UX Polish
- Add keyboard shortcuts for power users
- Implement undo/redo for answers
- Add "Save draft" functionality
- Improve error messages with helpful suggestions
- Add tooltips and contextual help

### 6.4: Accessibility
- Ensure CLI works with screen readers
- Add ARIA labels to web UI
- Keyboard navigation for all features
- High contrast mode support

---

## Success Criteria ✅

MVP is complete when:

1. **Interactive CLI**:
   - ✅ User can run `devussy interactive-design` and get guided through questions
   - ✅ Questions adapt based on previous answers
   - ✅ Session can be saved and resumed
   - ✅ Generated devplan reflects the interactive conversation

2. **Web Interface**:
   - ✅ FastAPI server running with question API
   - ✅ Simple web UI for question-by-question input
   - ✅ Real-time streaming of LLM generation via WebSocket
   - ✅ Authentication and rate limiting functional

3. **Documentation Alignment**:
   - ✅ DevPlan template reflects interactive approach
   - ✅ Handoff template provides context about interactive features
   - ✅ API documentation complete with examples

4. **Quality**:
   - ✅ 80%+ test coverage for new code
   - ✅ All existing tests still passing
   - ✅ Works on Windows, Mac, Linux
   - ✅ Comprehensive user documentation

---

## Non-Goals (Out of Scope for MVP)

❌ PyPI publication (nice-to-have, not critical for MVP)
❌ Advanced web UI framework (React/Vue) - vanilla JS is fine for MVP
❌ Multi-user support / database persistence
❌ Cloud deployment / hosting
❌ Mobile app
❌ Payment/subscription system

---

## Timeline Estimate

- **Phase 1**: 3-5 days (Interactive CLI)
- **Phase 2**: 5-7 days (Web Interface)
- **Phase 3**: 2-3 days (Template Alignment)
- **Phase 4**: 3-4 days (Smart Questions)
- **Phase 5**: 1-2 days (Documentation)
- **Phase 6**: 2-3 days (Testing & Polish)

**Total**: 16-24 days (~3-5 weeks for one developer)

---

## Next Immediate Steps

1. Start Phase 1.1: Design the interactive question flow
2. Map out essential vs optional questions
3. Create `docs/INTERACTIVE_FLOW.md` with the question tree
4. Begin implementing `src/interactive.py` module

---

## Notes

- **Backward compatibility**: Keep existing flag-based CLI commands working
- **Incremental delivery**: Each phase should be shippable
- **User feedback**: Test with real users after Phase 1 and Phase 2
- **Flexibility**: Question flow should be configurable via YAML/JSON
