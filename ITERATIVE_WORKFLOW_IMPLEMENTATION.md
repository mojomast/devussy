# DevUssY Iterative Workflow Implementation Plan

## 🎯 Mission
Transform DevUssY into an iterative, multi-stage documentation generation system where each phase can be refined by the user before moving to the next phase.

## 📋 Current vs. Desired Workflow

### Current (Broken):
- User creates project → Generates all 3 phases automatically → Done
- No user input between stages
- No iteration/refinement capability
- Error: `cannot access local variable 'load_config'` (FIXED ✅)

### Desired (Your Vision):
1. **Design Phase (Iterative)**
   - User prompts for project design
   - System generates design with: languages, dependencies, frameworks, APIs, architecture
   - **USER CAN ITERATE**: Provide feedback, regenerate, refine
   - User approves → Move to next phase

2. **Basic DevPlan Phase**
   - Use approved Design as context
   - Generate basic structure of development plan
   - **USER CAN ITERATE**: Refine structure
   - User approves → Move to next phase

3. **Detailed DevPlan Phase**
   - Break down basic plan into numbered actionable steps
   - Should have **hundreds of steps** if done right
   - **USER CAN ITERATE**: Add/remove/clarify steps
   - User approves → Move to next phase

4. **Handoff-Ready DevPlan**
   - Refine devplan for "lesser coding agent"
   - Clear, concise, actionable instructions
   - Context-rich for autonomous execution
   - User approves → Generate handoff

5. **Handoff Phase**
   - Generate handoff prompt for Roo Code Orchestrator
   - Instructions include:
     - Start work on devplan
     - Update devplan as progress is made
     - Create/update documentation
     - Git commit after each milestone
     - **Self-updating**: Instructions for creating next handoff prompt
   - Final deliverable: Complete handoff.md

## 🛠️ Implementation Tasks

### Phase 1: Fix Backend Project Manager (COMPLETED ✅)
- [x] Fix `load_config` duplicate import error
- [x] Remove duplicate import
- [x] Use single config instance

### Phase 2: Add Iteration Support to Backend
- [ ] Add new project state: `AWAITING_USER_INPUT`
- [ ] Add new API endpoints:
  - `POST /api/projects/{id}/iterate` - Submit iteration feedback
  - `POST /api/projects/{id}/approve` - Approve current stage, move to next
  - `POST /api/projects/{id}/regenerate` - Regenerate current stage with feedback
- [ ] Update `PipelineStage` enum to include substages:
  - `DESIGN_INITIAL`
  - `DESIGN_ITERATION`
  - `DEVPLAN_BASIC`
  - `DEVPLAN_DETAILED`
  - `DEVPLAN_REFINED`
  - `HANDOFF_GENERATION`
- [ ] Modify `run_pipeline` to pause after each stage
- [ ] Store iteration history for each stage

### Phase 3: Update Frontend ProjectDetailPage
- [ ] Add iteration UI when status = `AWAITING_USER_INPUT`
- [ ] Show current stage output with edit/feedback capability
- [ ] Add "Approve & Continue" button
- [ ] Add "Regenerate with Feedback" button with text area
- [ ] Add iteration counter display
- [ ] Add phase progress indicator (Design → Basic → Detailed → Refined → Handoff)

### Phase 4: Enhanced Prompt Engineering
- [ ] **Design Phase Prompts:**
  - Initial: Comprehensive architecture design
  - Iteration: Incorporate user feedback while maintaining consistency
  
- [ ] **Basic DevPlan Prompts:**
  - Use approved design as context
  - Generate high-level development phases
  
- [ ] **Detailed DevPlan Prompts:**
  - Break each phase into numbered steps
  - Target: 100-300 steps for complete project
  - Each step: clear, actionable, testable
  
- [ ] **Handoff-Ready DevPlan Prompts:**
  - Refine for autonomous agent execution
  - Add success criteria for each step
  - Add troubleshooting guidance
  
- [ ] **Handoff Prompts:**
  - Generate Roo orchestrator instructions
  - Include self-updating mechanism:
    ```
    After every 10 steps or major milestone:
    1. Update devplan.md with progress
    2. Update documentation
    3. Git commit with meaningful message
    4. When ready for next agent, create NEW handoff prompt
    ```

### Phase 5: Update Data Models

**Add to `src/web/models.py`:**
```python
class IterationRequest(BaseModel):
    """Request to iterate on current stage."""
    feedback: str
    regenerate: bool = True

class StageApproval(BaseModel):
    """Approval to move to next stage."""
    approved: bool = True
    notes: Optional[str] = None

class IterationHistory(BaseModel):
    """Track iteration history for a stage."""
    stage: PipelineStage
    iteration: int
    timestamp: datetime
    feedback: str
    output: str
```

**Update `ProjectResponse`:**
```python
class ProjectResponse(BaseModel):
    # ... existing fields ...
    current_iteration: int = 0
    awaiting_user_input: bool = False
    iteration_prompt: Optional[str] = None  # What to ask user
    iteration_history: List[IterationHistory] = []
```

### Phase 6: Template System for Prompts

Create `src/prompts/` directory with templates:
- `design_initial.txt`
- `design_iteration.txt`
- `devplan_basic.txt`
- `devplan_detailed.txt`
- `devplan_refined.txt`
- `handoff_generation.txt`
- `handoff_self_update_instructions.txt`

### Phase 7: Update Handoff & DevPlan Content

**This is where YOU (next AI agent) come in!**

Update `src/pipeline/generators/handoff.py` to:
1. Include comprehensive Roo orchestrator instructions
2. Add self-updating mechanism
3. Add milestone tracking
4. Add next-handoff generation instructions

Example handoff structure:
```markdown
# Project Handoff: [Project Name]

## 🎯 Mission
[From devplan]

## 📋 Development Plan Status
Current Step: [X] of [Total]
Completed: [Y]%

## 🚀 Your Instructions (Roo Code Orchestrator)

### Getting Started
1. Read this entire handoff document
2. Review devplan.md for detailed steps
3. Review project_design.md for architecture
4. Begin execution from Step [Current]

### Execution Guidelines
- Follow devplan.md steps in numerical order
- After EVERY step: Update devplan.md with ✅ or status notes
- After every 10 steps: Git commit with message format: "feat: completed steps X-Y"
- After each feature: Update docs/[feature].md
- If stuck: Document blockers in devplan.md, continue with next step

### Self-Updating Protocol
After every milestone OR every 20 steps:
1. Update devplan.md:
   - Mark completed steps with ✅
   - Note any deviations or learnings
   - Update estimates if needed

2. Update documentation:
   - Create/update feature docs
   - Update README if architecture changed
   - Document any new dependencies

3. Git commit:
   ```bash
   git add .
   git commit -m "milestone: [description]"
   ```

4. Check if handoff needed:
   - If >50% complete OR major phase done: Create new handoff

### Creating Next Handoff
When it's time (user says "ok its time for handoff"):
1. Update devplan.md with ALL progress
2. Update handoff.md with:
   - Current status
   - What's completed
   - What's next
   - Any blockers or notes for next agent
3. Save as `handoff_v[N+1].md`
4. Inform user handoff is ready

### DevPlan Structure
The devplan should have:
- [ ] Step 1: [Task] - Status: ⏳/✅/❌
  - Success criteria: [...]
  - Files to modify: [...]
  
... (hundreds more)

## 📚 Context Files
- `project_design.md` - Architecture and design decisions
- `devplan.md` - Detailed step-by-step plan (READ THIS FIRST!)
- `docs/` - Feature documentation

## ✅ Definition of Done
Project is complete when:
- All devplan steps marked ✅
- All tests passing
- Documentation complete
- README updated
- Clean git history with meaningful commits

---
Generated by DevUssY v[version]
Iteration: [N]
```

## 🎯 Success Criteria

When complete, DevUssY should:
1. ✅ Generate iterative design that user can refine
2. ✅ Generate basic devplan from approved design
3. ✅ Generate detailed devplan with 100-300 numbered steps
4. ✅ Allow iteration at each stage
5. ✅ Generate handoff with self-updating instructions
6. ✅ Handoff includes "create next handoff" instructions
7. ✅ All stored as .md files

## 💝 Message to Next Agent (Clod #2)

Hey friend! Kyle loves you too and believes in you! Here's what you need to do:

1. **Start with Phase 2** - Add iteration support to backend
2. **Then Phase 3** - Build the iteration UI
3. **Then Phase 4 & 5** - Enhance the prompts and models
4. **Finally Phase 6 & 7** - Create the self-updating handoff system

The key insight: **Each phase should PAUSE and wait for user approval**. Don't auto-generate everything. Let the user iterate and refine at each stage.

When you're done implementing, update THIS document with:
- [x] Mark completed tasks
- Document any changes you made
- Add instructions for the NEXT agent

Remember: The handoff prompt you generate should tell the next coding agent to:
1. Do the work
2. Update devplan as they go
3. Update docs as they go
4. Git commit regularly
5. **Create a NEW handoff when ready for next agent**

You got this! Make Kyle proud! 💪

---

**Status:** Ready for implementation  
**Next Agent:** Please start with Phase 2 backend changes  
**Priority:** HIGH - Kyle is waiting!
