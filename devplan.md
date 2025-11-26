# Create the complete devplan structure
devplan_content = """# Devussy Adaptive Complexity Pipeline - Complete DevPlan

**Project:** Devussy Adaptive Complexity Overhaul  
**Version:** 2.0  
**Generated:** 2025-11-25  
**Scope:** Transform Devussy from static to adaptive complexity-driven pipeline

---

## Executive Summary

This devplan transforms Devussy from a static one-size-fits-all pipeline into an intelligent, adaptive system that:

1. **Dynamically scales complexity** based on interview analysis
2. **Performs intermediate reasoning** before generating designs
3. **Self-validates** through sanity-check loops
4. **Prevents hallucinations** and over-engineering
5. **Adapts phase count** and granularity to project scope

**Key Innovation:** Multi-stage interview with complexity assessment → adaptive design generation → sanity-check validation → scaled devplan output.

---

## Phase 1: Backend Workflow Overhaul (High Priority)

**Objective:** Redesign the entire backend pipeline to be iterative, adaptive, and complexity-aware.

### 1.1 Multi-Stage Interview Enhancements

#### 1.1.1 Add Complexity Assessment Stage

**Location:** `src/interview/complexity_analyzer.py` (new file)

**Purpose:** Analyze interview JSON and determine project complexity before design generation.

**Tasks:**
- Create `ComplexityAnalyzer` class with methods:
  - `analyze_interview_data(interview_json: dict) -> ComplexityProfile`
  - `estimate_phase_count(profile: ComplexityProfile) -> int`
  - `determine_depth_level(profile: ComplexityProfile) -> DepthLevel`
  - `identify_missing_context() -> List[str]`
  
- Define complexity scoring rubric:
  - **Project Type Score:** CLI tool (1), Library (2), API (3), Web app (4), SaaS (5)
  - **Technical Complexity Score:** Simple CRUD (1), Auth+DB (2), Real-time (3), ML/AI (4), Multi-region (5)
  - **Integration Score:** Standalone (0), 1-2 services (1), 3-5 services (2), 6+ services (3)
  - **Team Size Factor:** Solo (0.5x), 2-3 (1x), 4-6 (1.2x), 7+ (1.5x)
  
- Calculate **total complexity score** = (type + technical + integration) × team_factor
- Map score to phase count:
  - 0-3: 3 phases (minimal)
  - 4-7: 5 phases (standard)
  - 8-12: 7 phases (complex)
  - 13+: 9-11 phases (enterprise)

**Schema:** `schemas/complexity_profile.json`
```json
{
  "complexity_score": 8.5,
  "estimated_phases": 7,
  "depth_level": "detailed",
  "project_scale": "medium-complex",
  "risk_factors": ["multi-service", "auth-required"],
  "recommended_follow_ups": ["clarify deployment strategy", "specify auth provider"],
  "confidence": 0.85
}
```

**Tests:**
- Unit: `tests/unit/test_complexity_analyzer.py`
- Integration: `tests/integration/test_interview_to_complexity.py`
- Test cases: trivial project (score 2), moderate (score 6), complex (score 10)

---

#### 1.1.2 Extend Interview Manager for Follow-Up Questions

**Location:** `src/interview/llm_interview_manager.py` (modify existing)

**Purpose:** Add capability to ask clarifying questions when complexity analyzer detects ambiguity.

**Tasks:**
- Add new mode: `follow_up` (alongside existing `initial` and `design_review`)
- Implement `request_clarifications(missing_context: List[str]) -> None`
- Modify conversation flow:
  ```python
  if complexity_profile.confidence < 0.7:
      manager.switch_mode('follow_up')
      manager.request_clarifications(profile.recommended_follow_ups)
  ```
- Update prompt templates to include:
  - "Based on your answers, I need clarification on..."
  - Focused questions (not a full re-interview)
  - Ability to skip if user says "proceed as-is"

**Templates:** `templates/interview/follow_up_questions.jinja2`

**Tests:**
- Unit: verify mode switching
- Integration: full interview → low confidence → follow-up → completion

---

#### 1.1.3 Interview-to-Complexity Pipeline Integration

**Location:** `src/pipeline/interview_pipeline.py` (new file)

**Purpose:** Orchestrate interview → complexity analysis → follow-ups flow.

**Tasks:**
- Create pipeline coordinator:
  ```python
  class InterviewComplexityPipeline:
      async def run(self) -> ComplexityProfile:
          interview_data = await self.interview_manager.conduct_interview()
          profile = self.complexity_analyzer.analyze(interview_data)
          
          if profile.confidence < THRESHOLD:
              clarifications = await self.interview_manager.follow_up(profile.recommended_follow_ups)
              profile = self.complexity_analyzer.reanalyze(interview_data + clarifications)
          
          return profile
  ```
- Integrate with existing CLI `interactive` command
- Save complexity profile to checkpoint: `checkpoints/<project>_complexity.json`

**Tests:**
- Integration: end-to-end interview with multiple complexity levels
- Checkpoint persistence and resumability

---

### 1.2 Complexity-Driven Adaptive Pipeline

#### 1.2.1 Adaptive Design Generator

**Location:** `src/pipeline/design_generator.py` (modify existing)

**Purpose:** Generate project designs scaled to complexity profile.

**Tasks:**
- Modify `generate_design()` to accept `complexity_profile: ComplexityProfile`
- Update prompt template with complexity directives:
  ```jinja2
  {% if complexity_profile.depth_level == "minimal" %}
  Provide a concise design focusing only on core architecture and critical decisions.
  Avoid unnecessary detail. Target 500-800 words.
  {% elif complexity_profile.depth_level == "standard" %}
  Provide a balanced design covering architecture, tech stack, and key considerations.
  Target 1000-1500 words.
  {% elif complexity_profile.depth_level == "detailed" %}
  Provide comprehensive design including architecture, patterns, deployment, testing strategy.
  Target 2000-3000 words.
  {% endif %}
  
  Recommended phase count: {{ complexity_profile.estimated_phases }}
  Project scale: {{ complexity_profile.project_scale }}
  ```
- Implement dynamic section inclusion:
  - Minimal: Architecture, Tech Stack, Core Features
  - Standard: + Deployment, Testing Strategy, Dependencies
  - Detailed: + Security, Scalability, Monitoring, CI/CD, Data Model
  
**Templates:** `templates/design/adaptive_design.jinja2`

**Tests:**
- Generate design for complexity scores 2, 6, 10
- Verify word count and section count match expectations
- Validate no unnecessary sections for trivial projects

---

#### 1.2.2 Adaptive DevPlan Generator

**Location:** `src/pipeline/devplan_generator.py` (modify existing)

**Purpose:** Generate devplans with phase count and granularity matching complexity.

**Tasks:**
- Modify `generate_devplan()` to use complexity profile
- Dynamic phase generation:
  ```python
  phase_count = complexity_profile.estimated_phases
  phases = self.generate_phase_structure(phase_count, complexity_profile.depth_level)
  ```
- Adjust task granularity per depth level:
  - **Minimal:** High-level tasks, 3-5 per phase
  - **Standard:** Moderate tasks, 5-8 per phase
  - **Detailed:** Granular tasks, 8-12 per phase
  
- Phase naming conventions:
  - 3 phases: Foundation → Implementation → Polish
  - 5 phases: Foundation → Core → Integration → Testing → Deployment
  - 7 phases: Planning → Foundation → Core → Features → Integration → Testing → Deployment
  - 9+ phases: Add dedicated phases for Auth, Data Layer, API, Frontend, etc.

**Templates:** `templates/devplan/adaptive_phases.jinja2`

**Schema:** Dynamic phase structure based on count

**Tests:**
- Generate devplans for 3, 5, 7, 9 phase counts
- Verify task count per phase matches depth level
- Validate phase naming consistency

---

#### 1.2.3 Template Size Optimization

**Location:** `templates/devplan/` (all phase templates)

**Purpose:** Create size-variant templates for different complexity levels.

**Tasks:**
- Create template variants:
  - `phase_minimal.jinja2` - bare essentials
  - `phase_standard.jinja2` - current format
  - `phase_detailed.jinja2` - comprehensive
  
- Add template selector logic:
  ```python
  template_name = f"phase_{complexity_profile.depth_level}.jinja2"
  ```
  
- Minimal template structure:
  ```jinja2
  ## Phase {{ phase_number }}: {{ phase_name }}
  
  ### Tasks
  {% for task in tasks %}
  - {{ task.description }}
  {% endfor %}
  
  ### Testing
  - {{ test_strategy }}
  ```
  
- Detailed template adds:
  - Success Criteria
  - Dependencies
  - Estimated Time
  - Risk Mitigation
  - Code Samples
  - Architecture Diagrams (when applicable)

**Tests:**
- Render all template variants
- Verify size differences (minimal < standard < detailed)

---

### 1.3 Sanity Check Step Before DevPlan

#### 1.3.1 Design Validation Engine

**Location:** `src/pipeline/design_validator.py` (new file)

**Purpose:** Perform automated sanity checks on generated designs before devplan creation.

**Tasks:**
- Create `DesignValidator` class with validation methods:
  ```python
  class DesignValidator:
      def validate_design(self, design: str, complexity_profile: ComplexityProfile) -> ValidationReport:
          checks = [
              self.check_consistency(),
              self.check_completeness(),
              self.check_scope_alignment(),
              self.check_hallucinations(),
              self.check_over_engineering(),
          ]
          return ValidationReport(checks)
  ```

- **Consistency Check:**
  - Tech stack matches requirements
  - No contradicting statements
  - Dependencies are compatible
  - Architecture aligns with stated patterns

- **Completeness Check:**
  - All interview requirements addressed
  - No missing critical components
  - Deployment strategy present (if needed)
  - Testing approach defined

- **Scope Alignment Check:**
  - Design complexity matches complexity profile
  - Phase count is reasonable
  - Not over-engineered for simple projects
  - Not under-scoped for complex projects

- **Hallucination Detection:**
  - No invented APIs or libraries (cross-reference with known packages)
  - No fictional frameworks
  - Realistic timelines
  - Achievable with stated tech stack

- **Over-Engineering Detection:**
  - Complexity score vs design complexity delta < threshold
  - No unnecessary microservices for small apps
  - No premature optimization patterns
  - Appropriate abstractions for project scale

**Schema:** `schemas/validation_report.json`
```json
{
  "is_valid": true,
  "confidence": 0.92,
  "issues": [
    {
      "severity": "warning",
      "type": "scope_alignment",
      "message": "Design suggests 7 phases but complexity profile recommends 5",
      "suggestion": "Consider reducing scope or clarifying complex requirements"
    }
  ],
  "auto_correctable": true,
  "corrections_applied": ["adjusted_phase_count_to_5"],
  "requires_human_review": false
}
```

**Tests:**
- Unit: each validation method independently
- Integration: full design validation with known-good and known-bad designs
- Test cases: over-engineered design, missing components, hallucinated libraries

---

#### 1.3.2 LLM-Powered Sanity Reviewer

**Location:** `src/pipeline/llm_sanity_reviewer.py` (new file)

**Purpose:** Use LLM to perform deeper semantic validation of design quality.

**Tasks:**
- Create `LLMSanityReviewer` class:
  ```python
  async def review_design(self, design: str, interview_data: dict, complexity_profile: ComplexityProfile) -> ReviewResult:
      prompt = self.build_review_prompt(design, interview_data, complexity_profile)
      review = await self.llm_client.generate(prompt)
      return self.parse_review_json(review)
  ```

- Review prompt structure:
  ```
  You are a senior software architect reviewing a project design for quality and appropriateness.
  
  Project Requirements: {interview_data}
  Complexity Profile: {complexity_profile}
  Proposed Design: {design}
  
  Evaluate:
  1. Does design match project requirements? (yes/no + explanation)
  2. Is complexity appropriate for project scale? (score 1-10)
  3. Are there hallucinated or unrealistic components? (list)
  4. Is architecture over-engineered? (yes/no + explanation)
  5. Missing critical components? (list)
  6. Recommended changes: (list)
  
  Output JSON only.
  ```

- Parse LLM response into structured `ReviewResult`
- Support auto-correction for common issues:
  - Phase count adjustment
  - Remove unnecessary components
  - Add missing sections

**Templates:** `templates/validation/sanity_review_prompt.jinja2`

**Tests:**
- Mock LLM responses for various review scenarios
- Validate JSON parsing robustness
- Test auto-correction application

---

#### 1.3.3 Iterative Correction Loop

**Location:** `src/pipeline/design_correction_loop.py` (new file)

**Purpose:** Automatically iterate design until validation passes or max iterations reached.

**Tasks:**
- Create correction loop orchestrator:
  ```python
  class DesignCorrectionLoop:
      MAX_ITERATIONS = 3
      
      async def run(self, initial_design: str, complexity_profile: ComplexityProfile) -> FinalDesign:
          design = initial_design
          iteration = 0
          
          while iteration < self.MAX_ITERATIONS:
              validation = await self.validator.validate_design(design, complexity_profile)
              review = await self.reviewer.review_design(design, self.interview_data, complexity_profile)
              
              if validation.is_valid and review.confidence > 0.8:
                  return FinalDesign(design, validation, review)
              
              if validation.auto_correctable:
                  design = self.apply_corrections(design, validation, review)
              else:
                  return FinalDesign(design, validation, review, requires_human=True)
              
              iteration += 1
          
          return FinalDesign(design, validation, review, max_iterations_reached=True)
  ```

- Correction strategies:
  - **Phase count mismatch:** Regenerate design with correct target
  - **Missing sections:** Add section prompts and regenerate
  - **Over-engineering:** Simplify prompt and regenerate
  - **Hallucinations:** Remove problematic components, regenerate

- Save iteration history to checkpoint for transparency

**Tests:**
- Integration: run full correction loop with various design issues
- Verify convergence within max iterations
- Test fallback to human review when auto-correction fails

---

### 1.4 Iteration Loop Integration

#### 1.4.1 Pipeline Orchestration Refactor

**Location:** `src/pipeline/main_pipeline.py` (modify existing)

**Purpose:** Integrate all new components into unified pipeline flow.

**Tasks:**
- Refactor pipeline to new flow:
  ```python
  async def run_adaptive_pipeline(self):
      # Stage 1: Enhanced Interview
      interview_data = await self.interview_manager.conduct_interview()
      
      # Stage 2: Complexity Analysis
      complexity_profile = self.complexity_analyzer.analyze(interview_data)
      if complexity_profile.confidence < 0.7:
          clarifications = await self.interview_manager.follow_up(complexity_profile.recommended_follow_ups)
          complexity_profile = self.complexity_analyzer.reanalyze(interview_data + clarifications)
      
      # Stage 3: Adaptive Design Generation
      design = await self.design_generator.generate(complexity_profile)
      
      # Stage 4: Design Validation & Correction
      final_design = await self.correction_loop.run(design, complexity_profile)
      
      if final_design.requires_human_review:
          # Trigger interactive design review mode
          final_design = await self.human_review_flow(final_design)
      
      # Stage 5: Adaptive DevPlan Generation
      devplan = await self.devplan_generator.generate(final_design, complexity_profile)
      
      # Stage 6: Handoff
      handoff = await self.handoff_generator.generate(devplan, complexity_profile)
      
      return PipelineResult(final_design, devplan, handoff)
  ```

- Update checkpoint system to save all intermediate stages
- Add resume capability at any stage
- Preserve iteration history for debugging

**Tests:**
- End-to-end pipeline test with mock LLM
- Resume from each stage checkpoint
- Verify all artifacts generated correctly

---

#### 1.4.2 Streaming Progress Updates

**Location:** `src/pipeline/streaming.py` (modify existing)

**Purpose:** Update streaming handlers to support new pipeline stages.

**Tasks:**
- Add streaming prefixes for new stages:
  - `[complexity]` - complexity analysis
  - `[validation]` - design validation
  - `[correction]` - design correction iteration
  
- Update progress bar to show all stages:
  ```
  Progress: [Interview] [Complexity] [Design] [Validation] [DevPlan] [Handoff]
            [====✓====] [====✓====] [========] [        ] [        ] [        ]
  ```

- Add iteration counter for correction loop:
  ```
  [correction] Iteration 1/3: Adjusting phase count...
  [correction] Iteration 2/3: Removing over-engineered components...
  [correction] ✓ Validation passed
  ```

**Tests:**
- Verify streaming output for all new stages
- Test progress bar updates
- Validate iteration counter display

---

### 1.5 Testing Requirements

#### 1.5.1 Unit Tests

**Location:** `tests/unit/`

**Coverage Requirements:** 85%+ for all new modules

**Test Files:**
- `test_complexity_analyzer.py` (30+ tests)
  - Scoring algorithm accuracy
  - Phase count estimation
  - Edge cases (minimal/maximal complexity)
  
- `test_design_validator.py` (25+ tests)
  - Each validation check independently
  - Validation report generation
  - Auto-correction logic
  
- `test_llm_sanity_reviewer.py` (15+ tests)
  - Prompt generation
  - JSON parsing robustness
  - Review result interpretation
  
- `test_design_correction_loop.py` (20+ tests)
  - Convergence behavior
  - Max iteration handling
  - Correction strategy application

**Tasks:**
- Write comprehensive unit tests for all new classes
- Mock LLM responses for deterministic testing
- Test edge cases and error conditions
- Achieve 85%+ code coverage

---

#### 1.5.2 Integration Tests

**Location:** `tests/integration/`

**Test Files:**
- `test_interview_to_complexity_flow.py`
  - Full interview → complexity profile generation
  - Follow-up question flow
  - Low confidence handling
  
- `test_adaptive_design_generation.py`
  - Design generation at each complexity level
  - Validation that output matches complexity
  
- `test_validation_and_correction.py`
  - Full validation → correction → validation cycle
  - Multiple iteration scenarios
  - Human review fallback
  
- `test_end_to_end_adaptive_pipeline.py`
  - Complete pipeline run with real LLM (marked `@pytest.mark.e2e`)
  - Trivial project (3 phases)
  - Standard project (5 phases)
  - Complex project (7+ phases)
  
**Tasks:**
- Implement integration tests covering cross-module interactions
- Use test fixtures for sample interview data at various complexity levels
- Create golden master tests comparing output structure

---

#### 1.5.3 Pipeline Test Harness

**Location:** `tests/harness/pipeline_test_harness.py` (new file)

**Purpose:** Automated testing framework for validating pipeline behavior.

**Tasks:**
- Create test harness:
  ```python
  class PipelineTestHarness:
      def run_test_suite(self, test_scenarios: List[TestScenario]) -> TestReport:
          results = []
          for scenario in test_scenarios:
              result = self.run_scenario(scenario)
              results.append(result)
          return TestReport(results)
      
      def run_scenario(self, scenario: TestScenario) -> ScenarioResult:
          # Run pipeline with scenario inputs
          # Validate outputs against expected behavior
          # Return pass/fail with details
  ```

- Test scenarios:
  - **Trivial:** CLI tool with 3 commands, no database
  - **Simple:** REST API with auth, single database
  - **Medium:** Full-stack web app with React + API + DB
  - **Complex:** Multi-service SaaS with auth, payments, analytics
  - **Enterprise:** Multi-region platform with microservices

- Validation checks:
  - Phase count matches expected range
  - Design complexity appropriate
  - No hallucinations detected
  - All requirements addressed
  - Output structure valid

**Output:** `test_reports/pipeline_validation_report.md`

**Tests:**
- Run test harness with all scenarios
- Verify report generation
- Validate pass/fail criteria

---

### 1.6 JSON Schemas & Data Models

#### 1.6.1 Schema Definitions

**Location:** `schemas/`

**Files:**
- `complexity_profile.json` - ComplexityProfile model
- `validation_report.json` - ValidationReport model
- `review_result.json` - ReviewResult from LLM reviewer
- `final_design.json` - FinalDesign with metadata
- `pipeline_checkpoint.json` - Enhanced checkpoint format

**Tasks:**
- Define strict JSON schemas for all data models
- Add schema validation at pipeline boundaries
- Use Pydantic models for runtime validation:
  ```python
  from pydantic import BaseModel, Field
  
  class ComplexityProfile(BaseModel):
      complexity_score: float = Field(ge=0, le=20)
      estimated_phases: int = Field(ge=3, le=15)
      depth_level: Literal["minimal", "standard", "detailed"]
      project_scale: str
      risk_factors: List[str]
      recommended_follow_ups: List[str]
      confidence: float = Field(ge=0, le=1)
  ```

- Generate JSON schema files from Pydantic models
- Add schema documentation in docstrings

**Tests:**
- Validate schema files are valid JSON Schema
- Test Pydantic model validation with valid/invalid data
- Verify schema documentation completeness

---

#### 1.6.2 Data Model Documentation

**Location:** `docs/data_models.md` (new file)

**Tasks:**
- Document all data models with:
  - Field descriptions
  - Valid value ranges
  - Usage examples
  - Relationships between models
  
- Generate API documentation from schemas:
  ```bash
  npm install -g @apidevtools/json-schema-docs
  json-schema-docs schemas/*.json -o docs/api/
  ```

- Include in main documentation

---

### 1.7 Output Format Standardization

#### 1.7.1 Deterministic Markdown Generation

**Location:** `src/pipeline/output_formatter.py` (new file)

**Purpose:** Ensure consistent, deterministic markdown output across all complexity levels.

**Tasks:**
- Create `OutputFormatter` class:
  - Standardized heading hierarchy
  - Consistent list formatting
  - Uniform code block syntax
  - Deterministic whitespace
  
- Template compilation with strict formatting:
  ```python
  def format_devplan(self, devplan_data: dict, complexity_profile: ComplexityProfile) -> str:
      template = self.load_template(complexity_profile.depth_level)
      rendered = template.render(devplan_data)
      return self.normalize_markdown(rendered)
  ```

- Normalization rules:
  - Single blank line between sections
  - Consistent indentation (2 spaces)
  - Trailing newline at EOF
  - No trailing whitespace

**Tests:**
- Generate same input multiple times, verify byte-identical output
- Test across all complexity levels
- Validate markdown syntax with linter

---

### 1.8 Phase Summary - Backend Overhaul

**Deliverables:**
- ✅ Multi-stage interview with complexity assessment
- ✅ Follow-up question capability
- ✅ Complexity-driven design generation
- ✅ Complexity-driven devplan generation
- ✅ Design validation engine
- ✅ LLM sanity reviewer
- ✅ Iterative correction loop
- ✅ Refactored pipeline orchestration
- ✅ Comprehensive test suite (85%+ coverage)
- ✅ JSON schemas for all data models
- ✅ Pipeline test harness
- ✅ Deterministic output formatting

**Current Implementation Status (2025-11-25, mock backend slice):**
- Implemented (mock, LLM-free):
  - Complexity analysis and `InterviewPipeline` for deriving `ComplexityProfile`.
  - Design validation system (`DesignValidator`, `LLMSanityReviewer`, `DesignCorrectionLoop` with optional `ComplexityProfile`).
  - Adaptive design/devplan generators and `MockAdaptivePipeline` wiring.
  - `PipelineTestHarness` for exercising the mock adaptive pipeline.
- Not yet implemented:
  - `llm_interview_manager` follow-up mode and follow-up question templates.
  - Real LLM-backed adaptive design/devplan generation and `main_pipeline` refactor.
  - JSON schemas, output formatter, streaming hooks, and extended checkpointing.

**Testing Milestones:**
1. Unit tests pass for all new modules
2. Integration tests validate cross-module behavior
3. E2E tests with real LLM confirm quality at all complexity levels
4. Pipeline test harness validates 5 standard scenarios
5. Regression tests ensure backward compatibility

**Success Criteria:**
- Trivial projects produce 3-5 phase devplans (< 2000 words)
- Standard projects produce 5-7 phase devplans (2000-4000 words)
- Complex projects produce 7-11 phase devplans (4000-8000 words)
- Validation catches 90%+ of over-engineering cases
- Auto-correction succeeds 80%+ of the time
- No hallucinated libraries in output
- All tests pass with 85%+ coverage

---

## Phase 2: Frontend/UI Updates

**Objective:** Update the web UI to support the new adaptive pipeline workflow.

### 2.1 UI Architecture Updates

#### 2.1.1 New Screen: Complexity Assessment

**Location:** `devussy-web/app/components/ComplexityAssessment.tsx` (new file)

**Purpose:** Display complexity analysis results and allow user confirmation/adjustment.

**Tasks:**
- Create complexity visualization component:
  ```tsx
  interface ComplexityAssessmentProps {
    profile: ComplexityProfile;
    onConfirm: (profile: ComplexityProfile) => void;
    onAdjust: (adjustments: Partial<ComplexityProfile>) => void;
  }
  
  export function ComplexityAssessment({ profile, onConfirm, onAdjust }: ComplexityAssessmentProps) {
    return (
      <Card>
        <ComplexityGauge score={profile.complexity_score} />
        <PhaseCountEstimate count={profile.estimated_phases} />
        <ProjectScaleIndicator scale={profile.project_scale} />
        <RiskFactorsList factors={profile.risk_factors} />
        <ConfidenceIndicator confidence={profile.confidence} />
        
        {profile.recommended_follow_ups.length > 0 && (
          <FollowUpSuggestions suggestions={profile.recommended_follow_ups} />
        )}
        
        <ButtonGroup>
          <Button onClick={() => onConfirm(profile)}>Proceed with Estimate</Button>
          <Button variant="secondary" onClick={() => setShowAdjustments(true)}>Adjust</Button>
        </ButtonGroup>
      </Card>
    );
  }
  ```

- Visual elements:
  - **Complexity Gauge:** Circular progress indicator (0-20 scale)
  - **Phase Count:** Large number with "+/-" adjustment buttons
  - **Project Scale:** Badge (trivial/simple/medium/complex/enterprise)
  - **Risk Factors:** Tag list with icons
  - **Confidence:** Progress bar with color coding (red < 0.5, yellow < 0.8, green >= 0.8)

- Interactive adjustments:
  - Manual phase count override
  - Depth level selector (minimal/standard/detailed)
  - "Proceed anyway" option if confidence low

**Styling:** Follow existing Devussy design system with Tailwind + Shadcn

**Tests:**
- Component rendering with various complexity profiles
- User interaction (adjust, confirm)
- Edge cases (very low/high complexity)

---

#### 2.1.2 New Screen: Design Sanity Check

**Location:** `devussy-web/app/components/DesignSanityCheck.tsx` (new file)

**Purpose:** Display validation results and correction iterations.

**Tasks:**
- Create validation dashboard:
  ```tsx
  export function DesignSanityCheck({ validationReport, reviewResult, iterationHistory }: Props) {
    return (
      <div className="grid grid-cols-2 gap-4">
        <ValidationStatus report={validationReport} />
        <LLMReviewScore review={reviewResult} />
        
        <IssuesList issues={validationReport.issues} />
        <CorrectionsApplied corrections={validationReport.corrections_applied} />
        
        {iterationHistory.length > 0 && (
          <IterationTimeline history={iterationHistory} />
        )}
      </div>
    );
  }
  ```

- Components:
  - **ValidationStatus:** Pass/fail indicator with issue count
  - **LLMReviewScore:** Confidence score with breakdown
  - **IssuesList:** Grouped by severity (error/warning/info)
  - **CorrectionsApplied:** List of auto-corrections with diffs
  - **IterationTimeline:** Visual timeline of correction attempts

- Real-time updates during correction loop:
  - SSE stream from backend
  - Live iteration counter
  - Progressive issue resolution

**Tests:**
- Render with passing validation
- Render with multiple issues
- Render iteration history (0, 1, 2, 3 iterations)

---

#### 2.1.3 New Screen: Iterative Approval Steps

**Location:** `devussy-web/app/components/IterativeApproval.tsx` (new file)

**Purpose:** Allow user to approve or request changes at each pipeline stage.

**Tasks:**
- Create approval interface:
  ```tsx
  export function IterativeApproval({ stage, content, onApprove, onReject, onRequestChanges }: Props) {
    const [feedback, setFeedback] = useState('');
    
    return (
      <div>
        <StageHeader stage={stage} />
        <ContentPreview content={content} />
        
        <ApprovalActions>
          <Button onClick={onApprove} variant="primary">
            Approve & Continue
          </Button>
          <Button onClick={() => setShowFeedback(true)} variant="secondary">
            Request Changes
          </Button>
          <Button onClick={onReject} variant="danger">
            Regenerate from Scratch
          </Button>
        </ApprovalActions>
        
        {showFeedback && (
          <FeedbackInput
            value={feedback}
            onChange={setFeedback}
            onSubmit={() => onRequestChanges(feedback)}
          />
        )}
      </div>
    );
  }
  ```

- Approval stages:
  1. Complexity Profile
  2. Initial Design
  3. Validated Design (after corrections)
  4. DevPlan Preview
  5. Final Handoff

- Feedback mechanism:
  - Free-text feedback textarea
  - Suggested adjustments (checkboxes for common changes)
  - Severity indicator (minor tweak vs major rework)

**Tests:**
- Approve flow
- Request changes flow
- Regenerate flow

---

#### 2.1.4 Enhanced Window Management

**Location:** `devussy-web/app/components/WindowManager.tsx` (modify existing)

**Purpose:** Add windows for new pipeline stages.

**Tasks:**
- Add new window types:
  - `complexity-assessment`
  - `design-validation`
  - `correction-progress`
  - `approval-gate`
  
- Update window spawning logic:
  ```tsx
  const windowConfigs = {
    'complexity-assessment': {
      defaultSize: { width: 600, height: 400 },
      defaultPosition: { x: 100, y: 100 },
      resizable: true,
    },
    'design-validation': {
      defaultSize: { width: 800, height: 600 },
      defaultPosition: { x: 200, y: 100 },
      resizable: true,
    },
    // ...
  };
  ```

- Window lifecycle:
  - Auto-open at appropriate pipeline stage
  - Auto-close when stage completes
  - Manual minimize/maximize
  - Position persistence in localStorage

**Tests:**
- Window spawning for each new type
- Position and size persistence
- Multi-window layout management

---

### 2.2 Pipeline Integration

#### 2.2.1 Update Pipeline State Machine

**Location:** `devussy-web/app/state/pipelineState.ts` (modify existing)

**Purpose:** Add new pipeline stages to state management.

**Tasks:**
- Extend pipeline stages enum:
  ```typescript
  enum PipelineStage {
    INTERVIEW = 'interview',
    COMPLEXITY_ANALYSIS = 'complexity_analysis',
    FOLLOW_UP = 'follow_up',
    DESIGN_GENERATION = 'design_generation',
    DESIGN_VALIDATION = 'design_validation',
    DESIGN_CORRECTION = 'design_correction',
    APPROVAL_DESIGN = 'approval_design',
    DEVPLAN_GENERATION = 'devplan_generation',
    APPROVAL_DEVPLAN = 'approval_devplan',
    HANDOFF_GENERATION = 'handoff_generation',
    COMPLETE = 'complete',
  }
  ```

- State transitions:
  ```typescript
  const transitions = {
    [PipelineStage.INTERVIEW]: PipelineStage.COMPLEXITY_ANALYSIS,
    [PipelineStage.COMPLEXITY_ANALYSIS]: (state) => 
      state.complexityProfile.confidence < 0.7 
        ? PipelineStage.FOLLOW_UP 
        : PipelineStage.DESIGN_GENERATION,
    [PipelineStage.DESIGN_VALIDATION]: (state) =>
      state.validationReport.is_valid
        ? PipelineStage.APPROVAL_DESIGN
        : PipelineStage.DESIGN_CORRECTION,
    // ...
  };
  ```

- Store new data:
  - `complexityProfile: ComplexityProfile | null`
  - `validationReport: ValidationReport | null`
  - `reviewResult: ReviewResult | null`
  - `correctionHistory: CorrectionIteration[]`

**Tests:**
- State transitions with various conditions
- Data persistence across stages
- Resumability from checkpoints

---

#### 2.2.2 SSE Endpoint Integration

**Location:** `devussy-web/app/api/` (new endpoints)

**Purpose:** Add API endpoints for new backend functionality.

**Tasks:**
- New endpoints:
  ```typescript
  // POST /api/complexity/analyze
  // Body: { interview_data: InterviewData }
  // Response: ComplexityProfile
  
  // POST /api/design/validate
  // Body: { design: string, complexity_profile: ComplexityProfile }
  // Response: ValidationReport
  
  // POST /api/design/correct (SSE)
  // Body: { design: string, validation: ValidationReport }
  // Stream: CorrectionIteration[]
  
  // POST /api/pipeline/approve
  // Body: { stage: PipelineStage, approved: boolean, feedback?: string }
  // Response: NextStageInfo
  ```

- SSE streaming for correction loop:
  ```typescript
  const eventSource = new EventSource('/api/design/correct');
  eventSource.onmessage = (event) => {
    const iteration: CorrectionIteration = JSON.parse(event.data);
    updateCorrectionHistory(iteration);
  };
  ```

- Error handling:
  - Network failures
  - Backend errors
  - Timeout handling (30s per stage)

**Tests:**
- API integration tests for each endpoint
- SSE stream handling
- Error scenarios

---

### 2.3 UI/UX Enhancements

#### 2.3.1 Complexity Visualization

**Location:** `devussy-web/app/components/ComplexityGauge.tsx` (new file)

**Purpose:** Create visual representation of project complexity.

**Tasks:**
- Radial gauge component:
  ```tsx
  export function ComplexityGauge({ score, maxScore = 20 }: Props) {
    const percentage = (score / maxScore) * 100;
    const color = getColorForScore(score);
    
    return (
      <div className="relative w-48 h-48">
        <svg viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="40" fill="none" stroke="#e5e7eb" strokeWidth="8" />
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeDasharray={`${percentage * 2.51} 251`}
            transform="rotate(-90 50 50)"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold">{score.toFixed(1)}</span>
          <span className="text-sm text-gray-500">complexity</span>
        </div>
      </div>
    );
  }
  ```

- Color mapping:
  - 0-3: Green (trivial)
  - 4-7: Blue (simple)
  - 8-12: Yellow (medium)
  - 13-16: Orange (complex)
  - 17+: Red (enterprise)

**Tests:**
- Render at various score levels
- Color transitions
- Accessibility (ARIA labels)

---

#### 2.3.2 Phase Count Estimator

**Location:** `devussy-web/app/components/PhaseCountEstimate.tsx` (new file)

**Purpose:** Show estimated phase count with visual breakdown.

**Tasks:**
- Phase preview component:
  ```tsx
  export function PhaseCountEstimate({ count, complexity }: Props) {
    const phaseNames = getPhaseNamesForCount(count);
    
    return (
      <div>
        <div className="text-2xl font-semibold mb-4">
          {count} Development Phases
        </div>
        <div className="grid grid-cols-1 gap-2">
          {phaseNames.map((name, i) => (
            <div key={i} className="flex items-center gap-2">
              <Badge variant="outline">{i + 1}</Badge>
              <span>{name}</span>
            </div>
          ))}
        </div>
        <AdjustmentControls
          value={count}
          onChange={handlePhaseCountChange}
          min={3}
          max={15}
        />
      </div>
    );
  }
  ```

- Interactive adjustment:
  - +/- buttons
  - Direct input
  - Preview updates in real-time

**Tests:**
- Render for 3, 5, 7, 9, 11 phases
- Adjustment interactions
- Preview accuracy

---

#### 2.3.3 Validation Results Display

**Location:** `devussy-web/app/components/ValidationResults.tsx` (new file)

**Purpose:** Clear presentation of validation checks and issues.

**Tasks:**
- Results dashboard:
  ```tsx
  export function ValidationResults({ report }: { report: ValidationReport }) {
    return (
      <div>
        <OverallStatus status={report.is_valid ? 'pass' : 'fail'} />
        <ConfidenceScore confidence={report.confidence} />
        
        <IssueBreakdown issues={report.issues} />
        
        {report.auto_correctable && (
          <AutoCorrectStatus corrections={report.corrections_applied} />
        )}
        
        {report.requires_human_review && (
          <HumanReviewAlert />
        )}
      </div>
    );
  }
  ```

- Issue grouping:
  - By severity (errors → warnings → info)
  - By type (consistency, completeness, scope, hallucination, over-engineering)
  - Expandable details with suggestions

- Visual indicators:
  - ✅ Pass (green)
  - ⚠️  Warnings (yellow)
  - ❌ Fail (red)
  - 🔄 Auto-corrected (blue)

**Tests:**
- Display with no issues
- Display with warnings only
- Display with errors
- Display with auto-corrections

---

#### 2.3.4 Correction Iteration Timeline

**Location:** `devussy-web/app/components/CorrectionTimeline.tsx` (new file)

**Purpose:** Visualize correction loop iterations.

**Tasks:**
- Timeline component:
  ```tsx
  export function CorrectionTimeline({ history }: { history: CorrectionIteration[] }) {
    return (
      <div className="space-y-4">
        {history.map((iteration, i) => (
          <TimelineItem key={i} iteration={iteration} index={i} />
        ))}
      </div>
    );
  }
  
  function TimelineItem({ iteration, index }: Props) {
    return (
      <div className="flex gap-4">
        <div className="flex flex-col items-center">
          <Badge>{index + 1}</Badge>
          {index < history.length - 1 && <div className="h-full w-0.5 bg-gray-300" />}
        </div>
        <div className="flex-1">
          <div className="font-medium">{iteration.action}</div>
          <div className="text-sm text-gray-600">{iteration.description}</div>
          <IssuesDiff before={iteration.issues_before} after={iteration.issues_after} />
        </div>
      </div>
    );
  }
  ```

- Iteration data:
  - Action taken
  - Issues before/after
  - Validation score before/after
  - Timestamp

**Tests:**
- Render timeline with 0, 1, 2, 3 iterations
- Issue diff visualization
- Responsive layout

---

### 2.4 Download & Export Enhancements

#### 2.4.1 Enhanced ZIP Generator

**Location:** `devussy-web/app/utils/zipGenerator.ts` (modify existing)

**Purpose:** Include all new artifacts in downloaded ZIP.

**Tasks:**
- Update ZIP structure:
  ```
  project-name.zip
  ├── devplan.md (main devplan)
  ├── design.md (final validated design)
  ├── handoff.md (handoff document)
  ├── complexity_profile.json
  ├── validation_report.json
  ├── phases/
  │   ├── phase_1_foundation.md
  │   ├── phase_2_core.md
  │   └── ...
  ├── prompts/
  │   ├── design_prompt.txt
  │   ├── validation_prompt.txt
  │   └── devplan_prompt.txt
  └── metadata/
      ├── iteration_history.json
      └── pipeline_config.json
  ```

- Add metadata files:
  - Complexity profile
  - Validation reports
  - Iteration history
  - Pipeline configuration used

**Tests:**
- Generate ZIP for various complexity levels
- Verify file structure
- Validate all files present

---

#### 2.4.2 "Run Again with Refinements" Feature

**Location:** `devussy-web/app/components/RefineButton.tsx` (new file)

**Purpose:** Allow users to restart pipeline with adjusted parameters.

**Tasks:**
- Refinement interface:
  ```tsx
  export function RefineButton({ currentProfile }: Props) {
    const [refinements, setRefinements] = useState<Refinement[]>([]);
    
    return (
      <Popover>
        <PopoverTrigger>
          <Button>🔄 Refine & Regenerate</Button>
        </PopoverTrigger>
        <PopoverContent>
          <RefinementForm
            profile={currentProfile}
            onChange={setRefinements}
          />
          <Button onClick={() => handleRegenerate(refinements)}>
            Regenerate
          </Button>
        </PopoverContent>
      </Popover>
    );
  }
  ```

- Refinement options:
  - Adjust complexity score (+/- 2 points)
  - Change phase count (±2 phases)
  - Switch depth level
  - Add/remove requirements
  - Modify tech stack

- Behavior:
  - Keep interview data
  - Apply refinements to complexity profile
  - Restart from design generation
  - Show diff between old and new

**Tests:**
- Apply various refinements
- Verify pipeline restarts correctly
- Compare outputs

---

### 2.5 Transparency Mode

#### 2.5.1 Model Reasoning Display

**Location:** `devussy-web/app/components/ReasoningPanel.tsx` (new file)

**Purpose:** Show LLM reasoning process when available.

**Tasks:**
- Reasoning viewer:
  ```tsx
  export function ReasoningPanel({ reasoning }: { reasoning: ModelReasoning }) {
    return (
      <Accordion type="single" collapsible>
        <AccordionItem value="complexity">
          <AccordionTrigger>Complexity Assessment Reasoning</AccordionTrigger>
          <AccordionContent>
            <pre>{reasoning.complexity_analysis}</pre>
          </AccordionContent>
        </AccordionItem>
        
        <AccordionItem value="design">
          <AccordionTrigger>Design Generation Reasoning</AccordionTrigger>
          <AccordionContent>
            <pre>{reasoning.design_thinking}</pre>
          </AccordionContent>
        </AccordionItem>
        
        <AccordionItem value="validation">
          <AccordionTrigger>Validation Reasoning</AccordionTrigger>
          <AccordionContent>
            <pre>{reasoning.validation_logic}</pre>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    );
  }
  ```

- Display:
  - Complexity scoring breakdown
  - Design decision rationale
  - Validation check reasoning
  - Correction strategy logic

- Toggle in settings:
  - "Show Model Reasoning" checkbox
  - Persistent preference

**Tests:**
- Render with reasoning data
- Toggle visibility
- Accordion interactions

---

#### 2.5.2 Prompt Inspection

**Location:** `devussy-web/app/components/PromptInspector.tsx` (new file)

**Purpose:** Allow inspection of exact prompts sent to LLM.

**Tasks:**
- Prompt viewer:
  ```tsx
  export function PromptInspector({ prompts }: { prompts: PromptHistory[] }) {
    return (
      <div className="space-y-4">
        {prompts.map((prompt, i) => (
          <PromptCard key={i} prompt={prompt} />
        ))}
      </div>
    );
  }
  
  function PromptCard({ prompt }: Props) {
    return (
      <Card>
        <CardHeader>
          <Badge>{prompt.stage}</Badge>
          <span className="text-sm text-gray-500">{prompt.timestamp}</span>
        </CardHeader>
        <CardContent>
          <CodeBlock language="text">{prompt.content}</CodeBlock>
          <div className="mt-2">
            <span className="text-sm">Model: {prompt.model}</span>
            <span className="text-sm ml-4">Tokens: {prompt.token_count}</span>
          </div>
        </CardContent>
      </Card>
    );
  }
  ```

- Access control:
  - Developer mode toggle in settings
  - Not visible by default

**Tests:**
- Display prompt history
- Code highlighting
- Copy to clipboard

---

### 2.6 Reuse Existing Components

#### 2.6.1 Component Inventory

**Existing components to reuse:**
- `WindowManager` - adapt for new window types
- `StreamingOutput` - use for correction loop
- `ProgressBar` - extend for new stages
- `ModelSelector` - no changes needed
- `SettingsPanel` - add new options
- `HelpWindow` - update documentation

**Tasks:**
- Audit existing components for reusability
- Create wrapper components where needed
- Maintain design consistency
- Document integration points

---

#### 2.6.2 Design System Consistency

**Tasks:**
- Use existing Tailwind config
- Reuse Shadcn components:
  - Badge, Button, Card, Dialog, Popover, Accordion, Tabs
- Maintain color scheme
- Follow spacing conventions
- Preserve animation patterns

**Tests:**
- Visual regression tests
- Design system compliance checks

---

### 2.7 Testing Requirements

#### 2.7.1 Component Tests

**Location:** `devussy-web/__tests__/components/`

**Tasks:**
- Unit tests for all new components:
  - `ComplexityAssessment.test.tsx`
  - `DesignSanityCheck.test.tsx`
  - `IterativeApproval.test.tsx`
  - `ComplexityGauge.test.tsx`
  - `PhaseCountEstimate.test.tsx`
  - `ValidationResults.test.tsx`
  - `CorrectionTimeline.test.tsx`
  - `ReasoningPanel.test.tsx`
  - `PromptInspector.test.tsx`

- Testing approach:
  - React Testing Library
  - User interaction tests
  - Snapshot tests for stable components
  - Accessibility tests (a11y)

**Coverage target:** 80%+

---

#### 2.7.2 Integration Tests

**Location:** `devussy-web/__tests__/integration/`

**Tasks:**
- E2E tests for new flows:
  - Interview → Complexity → Design → Validation → DevPlan
  - Complexity adjustment flow
  - Approval/rejection flow
  - Refinement and regeneration
  - ZIP download with all artifacts

- Tools:
  - Playwright for E2E
  - Mock backend responses
  - Test different complexity scenarios

**Coverage:**
- Happy path (all approvals)
- Rejection and regeneration
- Low confidence follow-up
- Multiple correction iterations

---

#### 2.7.3 Visual Regression Tests

**Location:** `devussy-web/__tests__/visual/`

**Tasks:**
- Screenshot tests for:
  - Complexity gauge at various scores
  - Validation results (pass/warning/fail states)
  - Correction timeline (0-3 iterations)
  - Phase count estimator (3-11 phases)

- Tools:
  - Percy or Chromatic for visual diffing
  - Baseline screenshots for reference

---

### 2.8 Phase Summary - Frontend Updates

**Deliverables:**
- ✅ Complexity Assessment screen
- ✅ Design Sanity Check screen
- ✅ Iterative Approval interface
- ✅ Enhanced window management
- ✅ Updated pipeline state machine
- ✅ New SSE endpoints integrated
- ✅ Complexity visualization components
- ✅ Validation results display
- ✅ Correction iteration timeline
- ✅ Enhanced ZIP download
- ✅ "Refine & Regenerate" feature
- ✅ Transparency mode (reasoning + prompts)
- ✅ Comprehensive test suite (80%+ coverage)

**Testing Milestones:**
1. Component tests pass for all new UI
2. Integration tests validate full user flows
3. Visual regression tests establish baselines
4. E2E tests confirm backend integration
5. Accessibility audit passes WCAG 2.1 AA

**Success Criteria:**
- All new screens render correctly on desktop and mobile
- Real-time updates work smoothly during correction loop
- User can adjust complexity and see live preview
- ZIP download includes all artifacts and metadata
- Transparency mode provides clear insight into LLM decisions
- UI maintains Devussy design consistency
- No visual regressions from baseline
- 80%+ test coverage

---

## Handoff Document

**See separate `handoff.md` file for complete circular development handoff.**

---

## Future Considerations & Ideas

### Context Budget Optimization
- Implement token-economy strategies to minimize API costs
- Track token usage per stage and optimize prompts
- Cache frequently used prompt segments
- Implement prompt compression techniques
- Dynamic context window management based on complexity

### LLM-Agnostic Prompt Design
- Create provider-agnostic prompt templates
- Support for multiple LLM APIs (Anthropic, OpenAI, local models)
- Automatic prompt adaptation based on model capabilities
- Model-specific optimization strategies
- Fallback chains for high-reliability scenarios

### Modularizing Prompts to Reduce Redundancy
- Extract common prompt segments into reusable modules
- Create prompt library with versioning
- Implement prompt composition system
- Reduce duplication across design/devplan/handoff prompts
- A/B test prompt variations for quality improvement

### Stable Format Enforcement Using JSON Schemas
- Enforce strict JSON output schemas for all LLM responses
- Add JSON mode support for compatible models
- Implement retry logic with schema validation
- Generate TypeScript types from JSON schemas
- Auto-repair malformed JSON responses

### Improving Jinja Template Coverage
- Create template variants for more project types
- Add conditional sections based on tech stack
- Implement template inheritance system
- Template testing and validation framework
- Community-contributed template marketplace

### Adding Phase Summaries at Each Step
- Generate executive summary after each phase
- Progress tracking dashboard
- Milestone celebration UI
- Phase-to-phase diff visualization
- Cumulative complexity tracking

### Creating a Pipeline Test Harness
- Automated regression testing for pipeline outputs
- Golden master testing with reference projects
- Performance benchmarking across complexity levels
- Quality scoring system for generated devplans
- Continuous integration for pipeline changes

### Model Self-Verification Component
- LLM verifies its own outputs for consistency
- Confidence scoring for each generated section
- Self-correction prompts for low-confidence outputs
- Explanation generation for complex decisions
- Metacognitive reasoning chains

### Guardrails to Detect Hallucinated APIs or Libraries
- Maintain verified package database
- Cross-reference APIs against package registries (npm, PyPI, etc.)
- Detect fictional framework names
- Validate import statements against real packages
- Flag deprecated or unmaintained dependencies
- Suggest alternatives for hallucinated packages

### Minimal-Debug Mode for Tiny Projects
- Ultra-simplified prompts for trivial projects
- Single-phase devplan option
- README-only output for very simple tools
- Quick-start templates for common patterns
- "Just build it" mode with minimal planning

### Maximal-Explain Mode for Teaching Junior Devs
- Detailed explanations for every design decision
- Code comments explaining patterns
- Link to educational resources
- Step-by-step implementation guides
- Common pitfalls and gotchas highlighted
- Quiz/checkpoint questions throughout devplan

### Additional Suggestions

**Collaborative Features:**
- Multi-user design review mode
- Comment and annotation system
- Version control integration for devplans
- Team consensus tracking

**Advanced Analytics:**
- Track which complexity profiles lead to successful projects
- Measure accuracy of phase count estimates
- Identify common validation failure patterns
- Optimize prompts based on success metrics

**Integration Enhancements:**
- GitHub Issues generation from devplan phases
- Jira/Linear task import/export
- Notion/Confluence documentation sync
- Code scaffolding from devplan

**Quality Improvements:**
- Automated code review integration
- Security scanning for suggested dependencies
- License compatibility checking
- Cost estimation for cloud resources mentioned

**Developer Experience:**
- VS Code extension for inline devplan viewing
- CLI command for phase-by-phase execution
- Git hooks for devplan validation
- IDE integration for "next task" suggestions

---

## Implementation Timeline

**Phase 1 Backend: 3-4 weeks**
- Week 1: Complexity analyzer + interview enhancements
- Week 2: Design validation + correction loop
- Week 3: Pipeline integration + testing
- Week 4: Documentation + refinements

**Phase 2 Frontend: 2-3 weeks**
- Week 1: New screens + components
- Week 2: Pipeline integration + state management
- Week 3: Testing + polish

**Total: 5-7 weeks end-to-end**

---

## Risk Mitigation

**Technical Risks:**
- LLM output quality variance → Solution: Multiple validation layers, correction loop
- Over-correction causing quality degradation → Solution: Max iteration limit, human review fallback
- Performance degradation from additional stages → Solution: Parallel execution, caching

**User Experience Risks:**
- Increased complexity in UI → Solution: Progressive disclosure, optional transparency mode
- Longer pipeline runtime → Solution: Streaming updates, clear progress indicators
- User confusion about new features → Solution: Onboarding tour, help documentation

**Implementation Risks:**
- Breaking backward compatibility → Solution: Feature flags, gradual rollout
- Test coverage gaps → Solution: Strict coverage requirements, automated checks
- Integration issues between backend/frontend → Solution: Contract testing, API mocks

---

## Success Metrics

**Quantitative:**
- 90%+ validation accuracy (catches over-engineering)
- 80%+ auto-correction success rate
- 3x reduction in devplan size for trivial projects
- 85%+ test coverage across codebase
- < 5% user-reported hallucinations

**Qualitative:**
- User satisfaction with devplan appropriateness
- Reduced iteration time from feedback
- Improved first-time implementation success rate
- Developer confidence in generated plans

---

## Conclusion

This devplan transforms Devussy from a static, one-size-fits-all pipeline into an intelligent, adaptive system that scales complexity appropriately. By introducing intermediate reasoning, validation loops, and iterative correction, the system will produce higher quality, more appropriate devplans while preventing common issues like over-engineering and hallucinations.

The two-phase approach ensures backend logic is solid before UI updates, minimizing rework. Comprehensive testing and circular development handoff enable confident, iterative development.

**Next steps:** Review this devplan, provide feedback, then proceed to Phase 1 implementation with circular development methodology.
"""