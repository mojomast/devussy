# Design Review Interview Fix Implementation (Hand-off)

This document captures the concrete code changes needed to turn the **Design Review Opportunity** step into a true design-review phase instead of repeating the initial requirements interview.

Files involved:
- `src/llm_interview.py`
- `src/cli.py` (interactive single-window workflow)

---

## 1. `LLMInterviewManager` changes (`src/llm_interview.py`)

### 1.1. Clean up and extend `__init__`

Inside `class LLMInterviewManager`, ensure the `__init__` method body looks like this (keep the existing imports and class docstring):

```python
def __init__(
    self,
    config: AppConfig,
    verbose: bool = False,
    repo_analysis: "RepoAnalysis | None" = None,
    markdown_output_manager: "MarkdownOutputManager | None" = None,
    mode: Literal["initial", "design_review"] = "initial",
):
    """Initialize with app config containing LLM settings.

    Args:
        config: Application configuration.
        verbose: Enable verbose logging / debug output.
        repo_analysis: Optional repository analysis used to prime the
            conversation with concrete project context.
        markdown_output_manager: Optional markdown output manager for
            saving responses.
        mode: "initial" for requirements gathering, or "design_review" for
            review of an existing design/devplan.
    """
    self.config = config
    self.verbose = verbose
    self.repo_analysis = repo_analysis
    self.markdown_output_manager = markdown_output_manager
    self.mode: Literal["initial", "design_review"] = mode

    self.llm_client = create_llm_client(config)

    # Apply debug/verbose flag to client (robust attribute discovery)
    self._apply_client_debug(verbose)

    # Core interview state
    self.conversation_history = []
    self.extracted_data = {}
    self.code_samples = []  # type: list[CodeSample]

    # Session-scoped interactive settings (not persisted)
    self.session_settings = SessionSettings()

    # Optional design-review specific context and extracted feedback
    self._design_review_context_md = None  # type: Optional[str]
    self._design_review_feedback = None    # type: Optional[Dict[str, Any]]

    # Track question counter for markdown output
    self.question_counter = 0

    # Setup logging
    self._setup_logging()

    # Add system prompt (core behavior), switched by mode
    if self.mode == "design_review":
        system_prompt = self.DESIGN_REVIEW_SYSTEM_PROMPT
    else:
        system_prompt = self.SYSTEM_PROMPT

    self.conversation_history.append({"role": "system", "content": system_prompt})

    # If repository analysis is available, prepend a concise summary so the
    # interview is repo-aware without changing the primary instructions.
    if self.repo_analysis is not None:
        summary = self._build_repo_summary(self.repo_analysis)
        if summary:
            self.conversation_history.append(
                {
                    "role": "system",
                    "content": (
                        "The user is working in the following existing project. "
                        "Use this context when asking questions and giving guidance.\n\n"
                        f"{summary}"
                    ),
                }
            )

    logger.info("LLM Interview Manager initialized")
    logger.info(f"Verbose mode: {self.verbose}")
    logger.info(f"Provider: {config.llm.provider}")
    logger.info(f"Model: {config.llm.model}")
```

Key points:
- No stray `self.*` lines at column 0 outside the method.
- Simple Python 3-compatible attributes; type comments used where needed.

---

### 1.2. Add `set_design_review_context()`

Immediately after `__init__`, add this method:

```python
# ------------------------------------------------------------------
# Design-review specific helpers
# ------------------------------------------------------------------

def set_design_review_context(
    self,
    design_md: str,
    devplan_md: Optional[str] = None,
    review_md: Optional[str] = None,
    repo_summary_md: Optional[str] = None,
) -> None:
    """Attach rich markdown context for design-review mode.

    The context is provided to the LLM at the beginning of the
    conversation when running in ``mode="design_review"`` so the
    assistant can act as a senior architect reviewing an existing
    proposal instead of gathering fresh requirements.
    """

    sections: list[str] = []

    # Artifact 1: Initial Project Design
    sections.append("## Artifact 1: Initial Project Design (v1)\n\n")
    sections.append((design_md or "_No design available._").strip())

    # Artifact 2: DevPlan Summary
    sections.append("\n\n## Artifact 2: DevPlan Summary\n\n")
    devplan_text = (devplan_md or "").strip() or "_No devplan summary available yet._"
    sections.append(devplan_text)

    # Artifact 3: Automatic Design Review
    sections.append("\n\n## Artifact 3: Automatic Design Review\n\n")
    review_text = (review_md or "").strip() or "_No automatic design review available._"
    sections.append(review_text)

    # Artifact 4: Repo Analysis Summary
    sections.append("\n\n## Artifact 4: Repo Analysis Summary\n\n")
    repo_text = (repo_summary_md or "").strip() or "_No repo analysis summary available._"
    sections.append(repo_text)

    preamble = (
        "Here is the current design and related context. "
        "Read this fully, then ask me clarifying questions as a senior "
        "architect before we finalize adjustments.\n\n"
    )

    self._design_review_context_md = preamble + "".join(sections)
```

---

### 1.3. Update `run()` to use design-review context

In `run()`, replace the initial section (up to the first LLM call) with:

```python
def run(self) -> Dict[str, Any]:
    """Run the conversational interview loop.

    Returns:
        Dict[str, Any]: Answers extracted from conversation
    """
    console.print(
        Panel.fit(
            "[bold blue]🚀 DevPlan Interactive Builder[/bold blue]\n"
            "Let's build your development plan together!\n\n"
            "[dim]Slash commands: /verbose, /help, /done, /quit, /settings, /model, /temp, /tokens[/dim]",
            border_style="blue",
        )
    )

    logger.info("Starting interview conversation")

    if self.repo_analysis:
        self._print_project_summary()

    # Start with initial greeting, customized by mode
    streaming_enabled = getattr(self.config, "streaming_enabled", False)

    if self.mode == "design_review" and self._design_review_context_md:
        # First, send the consolidated design context
        try:
            self._send_to_llm(self._design_review_context_md)
        except Exception:
            logger.exception("Failed to send design review context to LLM")

        # Then ask a focused opening question
        initial_response = self._send_to_llm(
            "I've reviewed the context you shared. "
            "Let's walk through any risks, gaps, or adjustments you'd recommend."
        )
        if not streaming_enabled:
            self._display_llm_response(initial_response)
    else:
        if (
            self.repo_analysis
            and getattr(self.repo_analysis, "project_metadata", None)
            and self.repo_analysis.project_metadata.name
        ):
            # Use the project name from repository analysis
            project_name = self.repo_analysis.project_metadata.name
            initial_response = self._send_to_llm(
                f"Hi! I'm excited to help you plan your project '{project_name}'. "
                f"I can see this is a {self.repo_analysis.project_type} project "
                f"with {self.repo_analysis.code_metrics.total_files} files. "
                "What would you like to accomplish with this project?"
            )
        else:
            # Ask for project name as before
            initial_response = self._send_to_llm(
                "Hi! I'm excited to help you plan your project. "
                "Let's start with the basics - what would you like to name your project?"
            )
        if not streaming_enabled:
            self._display_llm_response(initial_response)

    # ... keep the existing main loop and slash-command handling ...
```

At the **end** of `run()` (just before `return self.extracted_data`), add:

```python
    logger.info("Interview finished")

    # Best-effort extraction of design review feedback if in that mode
    if self.mode == "design_review":
        self._design_review_feedback = self._extract_design_review_feedback()

    return self.extracted_data
```

Make sure there is only one `logger.info("Interview finished")` in the method.

---

### 1.4. Add feedback extractor and public API

Add these methods near the other helpers in `LLMInterviewManager`:

```python
def _extract_design_review_feedback(self) -> Dict[str, Any]:
    """Scan conversation history for the final design-review JSON."""
    default: Dict[str, Any] = {
        "status": "ok",
        "updated_requirements": "",
        "new_constraints": [],
        "updated_tech_stack": [],
        "integration_risks": [],
        "notes": "",
    }

    # Look from last assistant message backward
    for msg in reversed(self.conversation_history):
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content") or ""
        if not content:
            continue

        candidate = None
        # Try pure JSON
        try:
            candidate = json.loads(content)
        except Exception:
            # Try to extract JSON blob inside fences or text
            m = re.search(r"\{.*\}", content, re.DOTALL)
            if m:
                try:
                    candidate = json.loads(m.group(0))
                except Exception:
                    candidate = None

        if not isinstance(candidate, dict):
            continue

        def _get(key: str, fallback: Any) -> Any:
            for k, v in candidate.items():
                if k.lower() == key:
                    return v
            return fallback

        def _as_list(value: Any) -> list[str]:
            if value is None:
                return []
            if isinstance(value, list):
                return [str(v).strip() for v in value if str(v).strip()]
            if isinstance(value, str):
                parts = re.split(r"[,\n]+", value)
                return [p.strip() for p in parts if p.strip()]
            return [str(value).strip()]

        return {
            "status": str(_get("status", default["status"]) or "ok"),
            "updated_requirements": str(
                _get("updated_requirements", default["updated_requirements"]) or ""
            ),
            "new_constraints": _as_list(
                _get("new_constraints", default["new_constraints"])
            ),
            "updated_tech_stack": _as_list(
                _get("updated_tech_stack", default["updated_tech_stack"])
            ),
            "integration_risks": _as_list(
                _get("integration_risks", default["integration_risks"])
            ),
            "notes": str(_get("notes", default["notes"]) or ""),
        }

    return default


def to_design_review_feedback(self) -> Dict[str, Any]:
    """Return structured design-review feedback (design_review mode only)."""
    if self.mode != "design_review":
        raise ValueError(
            "to_design_review_feedback() is only valid when mode='design_review'"
        )

    if self._design_review_feedback is None:
        self._design_review_feedback = self._extract_design_review_feedback()
    return self._design_review_feedback
```

This implements the JSON-extraction contract described in `interviewfix.md`.

---

## 2. CLI interactive design-review flow (`src/cli.py`)

In the `interactive()` command, after design generation, there is already a block that prints:

```python
print("[QUESTION] Design Review Opportunity")
...
conduct_design_review = input("\nEnter 'yes' to review, or press Enter to continue: ").strip().lower()

if conduct_design_review in ['yes', 'y']:
    print("\n[ROBOT] Starting design review interview...")
    ...
    review_manager = LLMInterviewManager(
        config=config,
        verbose=verbose,
        repo_analysis=repo_analysis,
        markdown_output_manager=markdown_output_mgr,
    )
    ...
    review_answers = await asyncio.to_thread(review_manager.run)
    if review_answers:
        ...
        review_data = review_manager.to_generate_design_inputs()
        ...
```

Replace that **entire** `if conduct_design_review in ...:` block with the following:

```python
if conduct_design_review in ["yes", "y"]:
    print("\n[ROBOT] Starting design review interview...")
    print("-" * 60)
    print("Review the generated design and provide feedback.")
    print("Type /done when you're finished with the review.\n")

    # Create a new interview manager for design review
    review_manager = LLMInterviewManager(
        config=config,
        verbose=verbose,
        repo_analysis=repo_analysis,
        markdown_output_manager=markdown_output_mgr,
        mode="design_review",
    )

    # Build rich design-review context
    try:
        design_md = markdown_output_mgr.load_stage_output("project_design")
    except Exception:
        # Fallback to a simple markdown from the structured design
        design_md = f"# Project Design: {design.project_name}\n\n{design.architecture_overview}\n"

    # Optional: placeholder values for future integration
    devplan_md = None
    review_md = None
    repo_summary_md = None

    review_manager.set_design_review_context(
        design_md=design_md,
        devplan_md=devplan_md,
        review_md=review_md,
        repo_summary_md=repo_summary_md,
    )

    try:
        # Run design review interview
        review_answers = await asyncio.to_thread(review_manager.run)

        if review_answers is not None:
            print("\n[OK] Design review completed!")

            feedback = review_manager.to_design_review_feedback()

            # Merge feedback into design_inputs
            if feedback.get("updated_requirements"):
                design_inputs["requirements"] += (
                    "\n\n[Design Review Adjustments]\n" + feedback["updated_requirements"].strip()
                )

            new_constraints = feedback.get("new_constraints") or []
            if new_constraints:
                constraint_block = "\n".join(f"- {c}" for c in new_constraints)
                design_inputs["requirements"] += (
                    "\n\n[Additional Constraints from Design Review]\n" + constraint_block
                )

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

            # Regenerate design with review feedback
            print("\n[REFRESH] Regenerating design with review feedback...\n")
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
            print("\n[OK] Updated design generated with review feedback!")

            # Save updated design - raw LLM response if available
            if getattr(design, "raw_llm_response", None):
                markdown_output_mgr.save_stage_output("design_review", design.raw_llm_response)
                logger.info(
                    "Saved raw LLM review response "
                    f"({len(design.raw_llm_response)} chars)"
                )
            else:
                # Fallback: reuse existing structured design save logic here
                # (keep or adapt your current structured save block)
                pass
        else:
            print("\n[NOTE] Design review cancelled, continuing with original design...")

    except Exception as e:
        logger.warning(f"Design review interview failed: {e}")
        print(f"\n[WARN] Design review failed: {e}")
        print("Continuing with original design...")
else:
    print("\n[OK] Skipping design review, continuing with original design...")
```

This makes the `yes` path:
- Run in `mode="design_review"` with the design-review system prompt.
- Provide the full design context via `set_design_review_context()`.
- Extract structured feedback with `to_design_review_feedback()`.
- Mutate `design_inputs` accordingly and regenerate a refined design.

---

## 3. Testing checklist

After implementing these changes, recommended tests:

1. **Unit tests for `LLMInterviewManager` design-review mode** (new file suggested):
   - `tests/test_llm_interview_design_review.py`
   - Use a fake/monkeypatched LLM client to push a known JSON block into `conversation_history`.
   - Assert `to_design_review_feedback()` returns the normalized dict with expected lists/strings.

2. **Integration sanity check**:
   - Run:

     ```bash
     python -m src.cli interactive
     ```

   - Go through the initial interview, allow design generation.
   - When prompted, answer `yes` to the design review.
   - Confirm that the second interview:
     - References the existing design instead of re-asking project name.
     - Ends with a JSON summary.
   - Confirm the regenerated design and subsequent devplan reflect the review feedback.

This `FIXX.MD` should be enough context for the next developer to implement and validate the design-review interview behavior end-to-end.
