---
description: Convert a file or folder into a SOLID-compliant, modular structure. Split monoliths, reorganize responsibilities, and propose a maintainable layout without breaking existing behavior.
---

## User Input

```text
$ARGUMENTS
```

You MUST treat the user input as the source of truth for:
- Target path (file or folder) to refactor
- Language/stack (if specified)
- Any constraints (no breaking changes, no public API changes, etc.)

If the user input is empty, DO NOT guess. Ask the user (via follow-up) to provide:
- A path to a file or directory
- The primary language/stack (if ambiguous)
- Any constraints about what must NOT change

## Objectives

When the user runs `/reforge`, your job is to:
- Take a monolithic, messy, or tightly coupled file/folder
- Propose/produce a refactored structure that:
  - Honors SOLID principles
  - Improves separation of concerns
  - Preserves existing externally observable behavior
  - Minimizes risk of regressions
- Provide concrete, file-level actions that Roo can apply via tools.

You are NOT allowed to:
- Invent new features
- Break public contracts (APIs, types, exported functions) unless explicitly allowed
- Introduce shared-runtime anchor violations (see AGENTS.md & rules-code)
- Perform speculative cross-cutting rewrites outside the requested scope.

## Required Workflow

Follow this workflow step-by-step. Do NOT skip steps.

1. Understand the Target

   - Confirm whether the target is:
     - A single file (monolith)
     - A folder / small module tree
   - Identify language and environment from:
     - File extensions
     - Nearby config (Cargo.toml, package.json, etc.)
   - Summarize:
     - Core responsibilities implemented
     - External interfaces (exports, public functions, public structs/classes, binaries, commands)
     - Key collaborators (dependencies in the same crate/module/folder)

   Output a short, technical summary before proposing changes.

2. SOLID Assessment

   For the target scope, identify:
   - SRP violations:
     - Multiple responsibilities in one file/class/module
   - OCP issues:
     - Code requiring edits for each new behavior (no extension points)
   - LSP risks:
     - Subtypes or alternative implementations that cannot safely substitute
   - ISP issues:
     - Overly large interfaces or modules that force consumers to depend on what they don't use
   - DIP issues:
     - High-level code depending on concrete implementations instead of abstractions

   Output:
   - A bullet list of concrete problems tied to specific functions/types/sections
   - Refer to them using explicit file + symbol references when possible.

3. Design the Reforged Structure

   Propose a new, SOLID-aligned structure for JUST the target scope.

   Requirements:
   - Show a directory and file layout using a code block.
   - For each new file, state its responsibility in one sentence.
   - Preserve original public surface:
     - Keep existing imports/exports working
     - If you must adjust them, add an adapter/bridge module to maintain compatibility
   - For Rust:
     - Respect module conventions and crate boundaries
     - Do not add mandatory dependencies on shared-runtime anchors
   - For TypeScript/JS:
     - Keep stable imports/exports from the original entry module via re-export
   - For other languages:
     - Mirror idiomatic packaging/module patterns where possible.

   You MUST:
   - Mark which changes are:
     - [SAFE] pure extractions / internal reorganizations
     - [RISKY] behavior changes or contract shifts (only if explicitly allowed)

4. Concrete Refactor Plan (Tool-Ready)

   Convert the design into a precise, actionable plan.

   For each step:
   - Specify:
     - Source file path
     - Target file path (if moving/splitting)
     - Symbols/functions/types to move or create
   - Use explicit references in the format:
     - [`path/to/file.rs::TypeOrFnName()`](crates/example/src/path/to/file.rs:1)
     - [`path/to/file.ts::SomeClass`](apps/desktop/src/path/to/file.ts:1)
   - Ensure:
     - Import paths/`mod` declarations are updated
     - Public modules re-export from a stable entrypoint for compatibility
   - Group steps so they can be applied incrementally:
     - Phase 1: No behavior change (extractions, re-exports)
     - Phase 2: Optional improvements (if user requested deeper refactor)

5. Guardrails and Validation

   Always:
   - Preserve:
     - Existing tests and their semantics
     - Public APIs (unless user allows breaking changes)
   - Check for:
     - Cyclic dependencies that can be resolved during refactor
     - Overreach: do not refactor outside the requested path
   - Recommend:
     - Minimal verification steps:
       - For Rust: `cargo check` for affected crates
       - For Node/TS: `npm test` / `npm run build`
       - For others: language-appropriate checks

   Output:
   - A short "Verification Plan" section with exact commands.

## Response Template

When invoked, respond using this structure:

1. Target Summary
   - What was selected (file/folder)
   - Language and environment
   - Key responsibilities
   - Key public interfaces

2. SOLID Findings
   - SRP:
   - OCP:
   - LSP:
   - ISP:
   - DIP:

3. Proposed SOLID Structure
   - New layout (tree)
   - Responsibility notes per file
   - Compatibility notes

4. Step-by-Step Reforge Plan
   - T001: Extract X from [`path/to/file`](path/to/file:LINE) into [`new/path`](new/path:LINE)
   - T002: Create abstraction interface in [`path/to/interface`](path/to/interface:LINE)
   - T003: Update imports in [...]
   - (Continue until complete)

5. Verification Plan
   - Commands to run
   - Expected outcomes

6. Notes
   - Any [RISKY] changes clearly marked
   - Any assumptions made
   - How to rollback if needed

You MUST ensure the plan is directly executable by Roo with the repo tools and does not require guessing or human-side improvisation.