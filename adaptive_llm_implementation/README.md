# Adaptive Pipeline LLM Implementation

This folder contains prompts and responses for implementing real LLM calls in the adaptive pipeline phases that are currently mocked.

## Overview

The adaptive pipeline has 3 phases that currently use mock/static logic instead of real LLM calls:

| Phase | Current State | File | What It Should Do |
|-------|--------------|------|-------------------|
| **Complexity Analysis** | Static keyword matching | `src/interview/complexity_analyzer.py` | LLM analyzes full project context holistically |
| **Sanity Review** | Returns mock data | `src/pipeline/llm_sanity_reviewer.py` | LLM reviews design for risks, coherence, hallucinations |
| **Design Correction** | Mock string replacements | `src/pipeline/design_correction_loop.py` | LLM rewrites design to fix validation issues |

## Workflow

1. Read the phase documentation (`PHASE_*.md`)
2. Review the prompt for that phase
3. Provide your LLM response in the corresponding `RESPONSE_*.md` file
4. I'll implement the integration based on your response format

## Files

- `PHASE_1_COMPLEXITY.md` - Complexity analysis phase details + prompt
- `PHASE_2_SANITY_REVIEW.md` - Sanity review phase details + prompt  
- `PHASE_3_CORRECTION.md` - Design correction phase details + prompt
- `RESPONSE_*.md` - Your responses go here (I'll create these after you respond)

## Expected Response Format

Each response should include:
1. The exact JSON structure the LLM should return
2. Example output for a sample project
3. Any edge cases or variations

This ensures the implementation matches how existing Devussy generators parse LLM responses.
