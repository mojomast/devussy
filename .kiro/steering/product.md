# Product Overview

Devussy is an LLM-based development planning orchestration tool that transforms project ideas into actionable development plans.

## Core Functionality

- **Multi-stage pipeline**: Design → Basic DevPlan → Detailed DevPlan → Handoff
- **Interview mode**: Analyzes existing codebases and generates context-aware devplans through interactive questioning
- **Terminal streaming UI**: Real-time generation of 5 concurrent phases (plan, design, implement, test, review) with live token output
- **Steering workflow**: Cancel phases mid-generation, provide feedback, and regenerate with context while other phases continue
- **Provider-agnostic**: Supports OpenAI, Generic OpenAI-compatible, Requesty, Aether AI, and AgentRouter
- **Resumable**: Checkpoint system allows resuming interrupted pipelines
- **Git-friendly**: Deterministic artifact generation to docs/ with optional git integration

## Key Features

- Async concurrency for parallel phase generation
- Live progress indicators with per-phase status and token usage tracking
- Update ritual system for maintaining artifact consistency
- Pre-review option to validate designs before planning
- Configurable task group sizes for iterative development
- Unified model picker across all configured providers
