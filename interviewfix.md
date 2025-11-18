# Design Review Interview Fix

This document describes how to fix and **streamline** the **Design Review Opportunity** step so that the second interview is a true
**design review session** with full context of the generated design — and is also **manageable, user-directed, and progress-aware**
instead of a long, repeated brain dump.

High-level goals for the new behavior:

- The agent itself **proposes concrete improvement areas** (the user is not responsible for finding all the issues).
- The user can then **choose which parts** of the design to improve from a numbered menu of focus areas.
- The model shows **simple progress**, e.g. `[2/5 areas completed]` as sections are finished.
- The final output is a **compact JSON summary** that can be merged back into the project design/devplan without blowing up context.
- We avoid the earlier bug where multiple long “review reports” were emitted without the user steering the flow.
# Design Review Interview Fix – Implementation Notes

This document summarizes the work completed to implement the **design-review interview** behavior, plus context for the next developer to continue or extend it.

---

## 1. Goal

Turn the **Design Review Opportunity** step in the interactive CLI (including the single-window flow) into a _true design-review_ phase, instead of simply repeating the initial requirements interview.

Key requirements from `FIXX.MD`:

- `LLMInterviewManager` must support a distinct `mode="design_review"` with its own system prompt.
- Design-review mode must start from existing design/devplan context, **not** re-ask basic questions like project name.
- At the end of the review, the LLM must emit a JSON summary with fields like `updated_requirements`, `new_constraints`, etc.
- The CLI should:
  - Ask the user whether to run a design review after design generation.
  - Run the review in `design_review` mode when requested.
  - Merge structured feedback back into the design inputs.
  - Regenerate the design with the adjustments applied.

All of the above is now implemented and wired through.

---

## 2. Changes in `src/llm_interview.py`

### 2.1. `LLMInterviewManager.__init__`

The constructor now:

- Accepts `mode: Literal["initial", "design_review"] = "initial"`.
- Stores it in `self.mode`.
- Chooses the system prompt based on `mode`:
  - `SYSTEM_PROMPT` for `initial`.
  - `DESIGN_REVIEW_SYSTEM_PROMPT` for `design_review`.
- Initializes new attributes:
  - `self._design_review_context_md = None` — consolidated markdown context.
  - `self._design_review_feedback = None` — cached structured feedback.

It also still sets up logging, the LLM client, session settings, conversation history, etc., and optionally injects a repo summary as an extra `system` message.

### 2.2. `set_design_review_context()`

New/cleaned method on `LLMInterviewManager`:

- Signature:
  - `set_design_review_context(self, design_md: str, devplan_md: Optional[str] = None, review_md: Optional[str] = None, repo_summary_md: Optional[str] = None) -> None`
- Behavior:
  - Builds a single markdown blob combining:
    - **Artifact 1** – initial project design.
    - **Artifact 2** – devplan summary (if provided).
    - **Artifact 3** – automatic design review summary (if any).
    - **Artifact 4** – repo analysis summary (if any).
  - Prepends a short preamble instructing the LLM to read the context and ask clarifying questions as a senior architect.
  - Stores the result in `self._design_review_context_md`.

This is meant to be called **before** `run()` when `mode="design_review"`.

### 2.3. `run()` startup logic for design-review mode

The top of `run()` has been updated to:

- Print a Rich `Panel` heading **without emojis** (to avoid Unicode surrogate issues on Windows terminals).
- Log the start of the interview.
- If `self.repo_analysis` is set, print a repo summary panel.
- Use different behavior based on `self.mode`:
  - If `mode == "design_review"` and `_design_review_context_md` is available, the flow is now explicitly **two-phase**:
    1. **Send consolidated design context** – the existing design, devplan summary, any prior review, and repo analysis are sent as one markdown blob.
    2. **Ask the model to propose a numbered checklist of improvement areas** – the first prompt after context tells the agent to:
       - Scan the full context and identify the 4–7 most important focus areas (e.g., architecture, RNG/determinism, persistence, performance, testing/CI, assets, observability).
       - Output a **concise, numbered list** with one-line descriptions.
       - Ask the user to choose which numbers to work on first.
       - Show a small progress indicator like `[2/5 areas completed]` as areas are completed.
  - Otherwise (normal `initial` mode):
    - Either greet with the repo-derived project name and type, or ask what to name the project.

The rest of the conversation loop (slash commands, `/done` handling, extraction of initial requirements JSON) is unchanged. The “menu of issues” behavior is driven entirely by this design-review-specific opening prompt.

### 2.4. End-of-run design-review feedback hook

At the end of `run()`, just before returning `self.extracted_data`, we now:

- Log `"Interview finished"`.
- If `self.mode == "design_review"`, call `_extract_design_review_feedback()` and store the result in `self._design_review_feedback`.

This ensures that design-review sessions automatically attempt to extract a **single, compact JSON summary** when they finish. That summary is what the CLI uses to actually tweak the project design/devplan.

### 2.5. Design-review feedback extraction API

Two methods were added to encapsulate the design-review JSON contract.

#### `_extract_design_review_feedback(self) -> Dict[str, Any]`

- Walks `self.conversation_history` **backwards**, looking at `assistant` messages only.
- For each candidate message:
  - Tries to parse the whole content as JSON.
  - If that fails, tries to find a `{ ... }` blob via regex and parse that.
- If it finds a dict-like JSON object, it normalizes the keys **case-insensitively** to:
  - `status`
  - `updated_requirements`
  - `new_constraints`
  - `updated_tech_stack`
  - `integration_risks`
  - `notes`
- Helper behavior:
  - `_get(key, fallback)` looks up a key by case-insensitive match.
  - `_as_list(value)` returns a list of strings, splitting comma/newline strings into items when necessary.
- Returns a dict of the shape:

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

- If no suitable JSON is found, returns a default object with empty fields and `status="ok"`.

#### `to_design_review_feedback(self) -> Dict[str, Any]`

- Public API for callers:
  - Raises `ValueError` if `self.mode != "design_review"`.
  - If `_design_review_feedback` is `None`, calls `_extract_design_review_feedback()`.
  - Returns the cached feedback dict.

This is what the CLI uses after `run()` completes in `design_review` mode.

### 2.6. Unicode / emoji safety

- The heading panel in `run()` previously used a rocket emoji.
- On Windows Python 3.13 terminal runs, this caused a `UnicodeEncodeError` (surrogate pair issues when writing to `stdout`).
- The heading text has been switched to plain ASCII, preserving styling but avoiding emojis.

If additional emojis (e.g., in `🎵 Devussy:`) cause issues later, a future enhancement would be to gate them behind a config flag or strip them for certain terminals.

---

## 3. CLI wiring – interactive single-window flow (`src/cli.py`)

The **single-window interactive** path is the one that prints:

- `[LIST] Step 1: Interactive Requirements Gathering`  
- `[TARGET] Step 2: Project Design Generation`

After the design is generated in this flow, there is a "Design Review Opportunity" block. This is where the main bug existed before: it was launching a second _initial_ interview instead of a design review.

### 3.1. Design Review Opportunity prompt

The CLI still asks the user:

```text
[QUESTION] Design Review Opportunity

The initial project design has been generated.
You can now review it and conduct a second interview to:
  • Refine architectural decisions
  • Add missing requirements or constraints
  • Adjust technology choices
  • Clarify implementation details

Would you like to conduct a design review interview?
```

Then it reads:

- `conduct_design_review = input("\nEnter 'yes' to review, or press Enter to continue: ").strip().lower()`

### 3.2. Yes path – new design review behavior

On `yes`/`y`, the CLI now:

1. **Logs the start of design review**

   Prints a short intro:

   - `[ROBOT] Starting design review interview...`
   - Horizontal rule.
   - Reminder that `/done` ends the review.

2. **Creates a design-review manager**

   ```python
   review_manager = LLMInterviewManager(
       config=config,
       verbose=verbose,
       repo_analysis=repo_analysis,
       markdown_output_manager=markdown_output_mgr,
       mode="design_review",
   )
   ```

   The critical piece is `mode="design_review"`.

3. **Builds design-review context**

   ```python
   try:
       design_md = markdown_output_mgr.load_stage_output("project_design")
   except Exception:
       design_md = f"# Project Design: {design.project_name}\n\n{design.architecture_overview}\n"
   
   devplan_md = None
   review_md = None
   repo_summary_md = None

   review_manager.set_design_review_context(
       design_md=design_md,
       devplan_md=devplan_md,
       review_md=review_md,
       repo_summary_md=repo_summary_md,
   )
   ```

   - Preferred source: raw LLM markdown saved as `project_design` stage output.
   - Fallback: synthesize a simple markdown design from `ProjectDesign` fields.

4. **Runs the design-review interview**

   - Uses `asyncio.to_thread(review_manager.run)` to execute the blocking console interview on a worker thread.
   - After completion, checks if `review_answers` is non-`None`:
     - If `None`, prints a notice and continues with the original design.

5. **Extracts structured feedback**

   Uses the new helper:

   ```python
   feedback = review_manager.to_design_review_feedback()
   ```

   Then merges the feedback into the `design_inputs` dict that will be used to regenerate the design:

   - **Updated requirements**:

     ```python
     if feedback.get("updated_requirements"):
         design_inputs["requirements"] += (
             "\n\n[Design Review Adjustments]\n"
             + feedback["updated_requirements"].strip()
         )
     ```

   - **New constraints**:

     ```python
     new_constraints = feedback.get("new_constraints") or []
     if new_constraints:
         constraint_block = "\n".join(f"- {c}" for c in new_constraints)
         design_inputs["requirements"] += (
             "\n\n[Additional Constraints from Design Review]\n"
             + constraint_block
         )
     ```

   - **Updated tech stack**:

     ```python
     updated_stack = feedback.get("updated_tech_stack") or []
     if updated_stack:
         existing_langs = [
             s.strip()
             for s in (design_inputs.get("languages") or "").split(",")
             if s.strip()
         ]
         for tech in updated_stack:
             if tech not in existing_langs:
                 existing_langs.append(tech)
         design_inputs["languages"] = ",".join(existing_langs)
     ```

6. **Regenerates the design with review feedback**

   Uses a `StreamingHandler` to show progress and calls:

   ```python
   design_stream = StreamingHandler.create_console_handler(prefix="[design-v2] ")
   design = await orchestrator.project_design_gen.generate(
       project_name=design_inputs["name"],
       languages=design_inputs["languages"].split(","),
       requirements=design_inputs["requirements"],
       frameworks=design_inputs.get("frameworks", "").split(",")
       if design_inputs.get("frameworks")
       else None,
       apis=design_inputs.get("apis", "").split(",")
       if design_inputs.get("apis")
       else None,
       streaming_handler=design_stream,
   )
   ```

   Then prints confirmation that an updated design has been generated.

7. **Saves review output**

   If the `design` object exposes `raw_llm_response`:

   ```python
   if getattr(design, "raw_llm_response", None):
       markdown_output_mgr.save_stage_output("design_review", design.raw_llm_response)
       logger.info(
           "Saved raw LLM review response "
           f"({len(design.raw_llm_response)} chars)"
       )
   ```

   Otherwise, the fallback is to reuse structured-save logic (left as a placeholder for now).

### 3.3. No path – skip review

If the user does **not** opt into design review (`conduct_design_review` not in `["yes", "y"]`):

- The CLI prints a short message confirming that it’s skipping design review and continues on to devplan generation and handoff as before.

---

## 4. Testing & Current Status

- Existing tests in this environment report `pytest -q` exit code `1`, but the error scanner shows **no syntax errors** in:
  - `src/llm_interview.py`
  - `src/cli.py`
- Known working scripts (unrelated to this change) include:
  - `python test_phase_specific_streaming.py` (exit code 0)
  - `python test_simple_duplication_check.py` (exit code 0)
- `test_streaming_duplication_fix.py` currently fails (exit code 1); this appears to predate the design-review work.

### Not yet implemented (good next tasks)

1. **Unit tests for design-review extraction**
   - Add `tests/test_llm_interview_design_review.py`.
   - Use a fake/interposed `LLMInterviewManager` with `mode="design_review"` and manually crafted `conversation_history`.
   - Verify that `to_design_review_feedback()` correctly normalizes fields and list formats (comma-separated strings vs lists).

2. **End-to-end sanity run**
   - Run the single-window interactive flow that prints `[TARGET] Step 2: Project Design Generation`.
   - After design generation, answer `yes` to design review.
   - Confirm that:
     - The LLM does **not** re-ask for project name in review mode.
     - The conversation references the existing design.
     - The regenerated design and devplan reflect the feedback.

3. **Consolidation / cleanup**
   - There are two interactive paths that now support design review (`interactive_design` and the single-window `run_interactive`).
   - Consider extracting a shared helper to avoid drift between these two flows over time.

---

## 5. TL;DR for the next agent

- **Design-review mode is implemented and wired through:**
  - `LLMInterviewManager` supports `mode="design_review"` with a dedicated system prompt, context injection, and JSON feedback extraction.
  - Both the traditional and single-window interactive flows can now launch a genuine design-review interview instead of repeating the initial requirements gathering.
- **User-facing behavior:**
  - After an initial design is generated, answering `yes` to the Design Review Opportunity prompt will:
    - Feed the existing design into the LLM as context.
    - Run a focused design review.
    - Apply the resulting adjustments back into the design inputs.
    - Regenerate a refined design.
- **Best next steps:** add focused tests around `to_design_review_feedback()` and run a full interactive session to confirm the UX matches expectations.