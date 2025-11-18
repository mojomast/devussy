# Design Review Interview Fix

This document describes how to fix the **Design Review Opportunity** step so that the second interview is a true **design review session** with full context of the generated design, rather than a repeat of the initial requirements interview.

---

## 1. Current Problem (What’s Broken)

**Symptoms**
- After the initial design is generated, the pipeline prints:
  - `Design Review Opportunity` → `Enter 'yes' to review, or press Enter to continue:`
- If the user enters `yes`, the system starts another `LLMInterviewManager` session.
- This second session mostly behaves like the **initial interview**:
  - Same generic system prompt focused on gathering project requirements.
  - No dedicated design-review question flow.
  - Only a small ad‑hoc text context is provided about the design.

**Result:** The second interview does **not** behave like a focused design review of the generated design/devplan; it feels like a repeat of the first interview with minimal awareness of the existing design docs.

---

## 2. High-Level Goal (What We Want)

Turn the "Design Review Opportunity" step into a proper **design review mode**:

- The second interview must:
  - Receive **rich context**: initial design, any automated design review, devplan summary, and repo analysis.
  - Use a **different system prompt**: act as a senior architect reviewing a proposed design, not as a requirements-gathering bot.
  - Produce a **different output shape**: design review feedback and adjustments, not fresh initial design inputs.
  - Feed that feedback back into the pipeline **before** generating devplan and phase docs.

---

## 3. Key Files Involved

These are the main files you’ll need to touch:

1. `src/llm_interview.py`
   - Defines `LLMInterviewManager` and its system prompt / interview flow.
2. `src/cli.py`
   - Contains the `Design Review Opportunity` prompt and logic to start the second interview.
   - There are **two** relevant flows:
     - Older sync flow around `typer.confirm("Would you like to conduct a design review interview?")` (~line 2490+).
     - Newer async pipeline flow around the `input("Enter 'yes' to review, or press Enter to continue: ")` (~line 3570+).
3. `src/pipeline/design_review.py`
   - Defines `DesignReviewRefiner`, which already runs an **automatic** LLM design review using `templates/design_review.jinja`.
4. `templates/design_review.jinja`
   - Prompt template used by `DesignReviewRefiner` for automatic (non-interactive) design review.
5. `src/prompts/design_iteration.txt`
   - Prompt template for refining a design based on user feedback; can be used to synthesize a **Design v2** after the interactive review.
6. `src/terminal/interview_ui.py` (optional)
   - If the TUI needs to support design review mode, similar changes may be applied here after the CLI flow is working.

---

## 4. New Concept: Design Review Mode on LLMInterviewManager

### 4.1 Add a Mode Flag ✅ (implemented)

In `src/llm_interview.py`, `LLMInterviewManager` now supports **modes**:

- `__init__` takes `mode: Literal["initial", "design_review"] = "initial"`.
- `self.mode` is stored and used to switch behavior.

### 4.2 Add a Design-Review System Prompt ✅ (implemented)

In `src/llm_interview.py`:

- `DESIGN_REVIEW_SYSTEM_PROMPT` has been added as a class-level constant.
- When `mode == "design_review"`, the manager now uses `DESIGN_REVIEW_SYSTEM_PROMPT` instead of `SYSTEM_PROMPT`.

The prompt already:
- Positions the LLM as a **senior architect** doing a design review.
- Explains that it will receive design artifacts.
- Emphasizes not re-asking basic project info unless inconsistent.
- Describes the shape of the final JSON feedback:
  - `status`, `updated_requirements`, `new_constraints`, `updated_tech_stack`, `integration_risks`, `notes`.

### 4.3 Add a Method to Inject Design Context ❗ (next agent)

Status: **not yet implemented**.

Target change in `src/llm_interview.py`:

- Add a method on `LLMInterviewManager`:
  - `set_design_review_context(design_md: str, devplan_md: str | None = None, review_md: str | None = None, repo_summary_md: str | None = None) -> None`
- Store these markdown blobs and build a single consolidated markdown string:
  - `## Artifact 1: Initial Project Design (v1)` → `design_md` or `_No design available._`.
  - `## Artifact 2: DevPlan Summary` → `devplan_md` or `_No devplan summary available yet._`.
  - `## Artifact 3: Automatic Design Review` → `review_md` or `_No automatic design review available._`.
  - `## Artifact 4: Repo Analysis Summary` → `repo_summary_md` or `_No repo analysis summary available._`.
- Prepend a short preamble, e.g.:
  - `Here is the current design and related context. Read this fully, then ask me clarifying questions as a senior architect before we finalize adjustments.`
- Store the final blob as `self._design_review_context_md`.
- In `run()`, before the normal greeting, if `mode == "design_review"` **and** `self._design_review_context_md` is set:
  - Call `self._send_to_llm(self._design_review_context_md)` as the first message.
  - Do **not** ask for project name; just let the model respond to the context.

### 4.4 Add a Design Review Output Mapper ❗ (next agent)

Status: **not yet implemented**.

Current state:
- `DESIGN_REVIEW_SYSTEM_PROMPT` already describes the required JSON shape at the end of the review.
- There is **no** `to_design_review_feedback()` yet, and no logic to scan the transcript for that JSON.

Target change in `src/llm_interview.py`:

1. Add a private helper:
   - `_extract_design_review_feedback() -> Dict[str, Any]`
   - Scan `self.conversation_history` **from last to first** for `role == "assistant"`.
   - For each candidate `content`:
     - Try `json.loads(content)`.
     - If that fails, optionally try to extract a `{...}` JSON object with a lightweight regex.
     - Expect keys (case-insensitive):
       - `status`, `updated_requirements`, `new_constraints`, `updated_tech_stack`, `integration_risks`, `notes`.
     - Normalize into:
       ```python
       {
           "status": str,
           "updated_requirements": str,
           "new_constraints": list[str],
           "updated_tech_stack": list[str],
           "integration_risks": list[str],
           "notes": str,
       }
       ```
     - For list fields, accept comma/newline-separated strings and coerce them to `list[str]`.
   - If nothing is found, return a default:
     ```python
     {
         "status": "ok",
         "updated_requirements": "",
         "new_constraints": [],
         "updated_tech_stack": [],
         "integration_risks": [],
         "notes": "",
     }
     ```

2. Add a public method:
   - `to_design_review_feedback() -> Dict[str, Any]`
   - Requires `self.mode == "design_review"`; otherwise raise `ValueError`.
   - Cache the result in `self._design_review_feedback` so multiple calls are cheap.
   - Optionally call `_extract_design_review_feedback()` once at the end of `run()` when `mode == "design_review"`.

---

## 5. Upgrade the CLI Design Review Flow

There are two places to update in `src/cli.py`.

### 5.1 Older Typer-Based Flow (Sync)

Around ~line 2490 (`typer.confirm("Would you like to conduct a design review interview?", ...)`):

1. **Construct a rich design context markdown**:
   - Use `markdown_output_mgr` (or equivalent) to load:
     - `project_design` output (already saved as markdown).
     - `design_review` report from `DesignReviewRefiner` if it exists.
     - Any devplan summaries if available at that point.
   - Build a consolidated `design_context_md` string as described in §4.3.

2. **Create the LLMInterviewManager in design review mode**:
   - Instantiate with `mode="design_review"`.
   - Call `review_manager.set_design_review_context(design_context_md, devplan_md, auto_review_md, repo_summary_md)`.

3. **Run the interview**:
   - Call `review_manager.run()` as today (or async variant in the newer flow).

4. **Extract design review feedback**:
   - Replace `review_manager.to_generate_design_inputs()` with `review_manager.to_design_review_feedback()`.

5. **Merge feedback into design inputs**:
   - If `updated_requirements` is present:
     - Append to existing `design_inputs["requirements"]` under a clearly marked section, e.g. `"[Design Review Adjustments]"`.
   - If `new_constraints` is present:
     - Append them as a bullet list under a `[Additional Constraints from Design Review]` section.
   - If `updated_tech_stack` is present:
     - Normalize and update `design_inputs["languages"]` or a `tech_stack` field appropriately.

6. **Optionally rerun design generation**:
   - If `status == "needs-changes"`, trigger a **design v2** generation before proceeding to devplan.
   - Optionally log both v1 and v2 designs and mark them in the markdown outputs.

### 5.2 Newer Async Pipeline Flow (Input("Enter 'yes' to review"))

Around ~line 3570+ in `src/cli.py` where you already have:

- The prompt block:
  - `Enter 'yes' to review, or press Enter to continue:`
- The newer logic that:
  - Creates `review_manager = LLMInterviewManager(config=..., repo_analysis=..., markdown_output_manager=markdown_output_mgr)`
  - Builds a `design_context` string from `design_inputs` + `design` object.
  - Calls `await asyncio.to_thread(review_manager.run)`.
  - Calls `review_manager.to_generate_design_inputs()` and then regenerates the design.

Update this block similar to the sync flow:

1. Switch the manager construction to `mode="design_review"`.
2. Upgrade `design_context` from a simple snippet to the richer consolidated markdown described earlier.
3. Call `review_manager.set_design_review_context(...)` before `run`.
4. After `run`, call `review_manager.to_design_review_feedback()`.
5. Merge feedback into `design_inputs` (requirements/constraints/tech stack) as in §5.1.
6. Keep the **regenerate design** step, but now use the updated `design_inputs` and, if desired, feed both original design and feedback through `design_iteration.txt` to craft a sharper `design_v2`.

---

## 6. Integrate With DesignReviewRefiner (Optional but Recommended)

You already have an automatic design review in `src/pipeline/design_review.py` using `DesignReviewRefiner` and `templates/design_review.jinja`.

To maximize value:

1. **Run automatic review first** (if not too slow):
   - After the initial design is generated and before asking the user about the design review interview, call `DesignReviewRefiner.refine(project_design)`.
   - Save the markdown report as stage `design_review` (e.g., `markdown_output_mgr.save_stage_output("design_review", report_md)`).

2. **Include this report in the design review context**:
   - When building `design_context_md` for `set_design_review_context`, include `design_review` content as `Artifact 3`.

3. **Optionally use `design_iteration.txt`**:
   - After collecting interactive feedback (`to_design_review_feedback()`), call a separate LLM generation using `src/prompts/design_iteration.txt`.
   - Inputs:
     - `original_design` = current design markdown (possibly including automatic refiner update).
     - `user_feedback` = pretty-printed summary from `to_design_review_feedback()`.
   - Use this to generate a **refined design v2** that is fully consistent.

---

## 7. Testing & Validation

Add/extend tests to ensure the new behavior works and doesn’t regress the pipeline.

1. **Unit-level tests for design review mode**:
   - In a new or existing test module (e.g., `tests/test_llm_interview_design_review.py`):
     - Construct `LLMInterviewManager(mode="design_review")` with a fake LLM client or monkeypatched generate method.
     - Call `set_design_review_context("design_md", "devplan_md", "review_md", "repo_summary_md")`.
     - Simulate a conversation and verify that `to_design_review_feedback()` returns a dict with the expected keys.

2. **Integration-like test of CLI flow**:
   - In `tests/integration/test_interactive_command_integration.py` (or a new test):
     - Mock initial `design_inputs` and `ProjectDesign`.
     - Mock `LLMInterviewManager` to:
       - Run in `design_review` mode.
       - Return a known `design_review_feedback` dict.
     - Run the CLI pipeline up through the design review step.
     - Assert that:
       - `design_inputs["requirements"]` now includes a `Design Review Adjustments` section.
       - Any `new_constraints` are present in the merged requirements or constraints field.
       - The updated inputs are used when regenerating the design.

3. **Manual sanity check**:
   - Run the pipeline interactively.
   - Accept the `Design Review Opportunity`.
   - Confirm that:
     - The LLM starts by summarizing/asking about the existing design.
     - It does **not** ask for basic project name/language again unless needed.
     - Devplan and phases reflect any changes from the review.

---

## 8. Summary for Next Agent

- **Goal:** Make the second interview a true design review, not a repeat requirements interview.
- **Core changes:**
  - Add `mode="design_review"`, `DESIGN_REVIEW_SYSTEM_PROMPT`, `set_design_review_context`, and `to_design_review_feedback()` to `LLMInterviewManager`.
  - Update both CLI flows that ask "Design Review Opportunity" to:
    - Instantiate the manager in design review mode.
    - Provide full design/devplan/review context.
    - Use `to_design_review_feedback()` to mutate `design_inputs`.
    - Regenerate design before devplan/phase generation.
  - Optionally integrate `DesignReviewRefiner` and `design_iteration.txt` for an automatic plus interactive refinement loop.

Once these steps are implemented, the pipeline’s second interview will reliably help users **find issues with the design and ensure everything will work together** before committing the devplan and generating phase docs.