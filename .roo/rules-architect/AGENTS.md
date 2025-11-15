# Architect Mode Rules (Non-Obvious Only)

## Architecture Overview
- **Multi-stage pipeline**: Design → Basic DevPlan → Detailed DevPlan → Handoff with checkpoint persistence
- **Provider-agnostic design**: `src/clients/factory.py` handles provider switching automatically
- **Async-first architecture**: All heavy operations use asyncio with proper event loop management
- **Template-driven generation**: Jinja2 templates with circular macro support for document generation

## Critical Architectural Constraints
- **Stateless providers**: LLM clients must be stateless - hidden caching layer assumes this
- **Provider switching**: Model selection automatically switches provider - architecture accounts for dynamic provider changes
- **File validation**: DevPlan generation requires specific content anchors (`<!-- PROGRESS_LOG_START -->`)
- **Checkpoint format**: State persistence follows `<project_name>_pipeline` pattern for consistency

## Component Architecture
- **Orchestrator pattern**: `src/pipeline/compose.py` - `PipelineOrchestrator` coordinates all stages
- **Concurrency control**: `src/concurrency.py` - `ConcurrencyManager` limits parallel operations
- **Repository analysis**: `src/interview/repository_analyzer.py` provides context for all pipeline stages
- **Safe file operations**: `src/file_manager.py` ensures data integrity with .bak files and validation

## Performance Architecture
- **Parallel phase generation**: Default 5 concurrent requests for detailed devplan creation
- **High token limits**: 81920+ tokens for detailed devplan generation (configurable per stage)
- **Streaming architecture**: Real-time token display via `StreamingHandler` with async context managers
- **Memory management**: Streaming handlers prevent memory leaks through proper cleanup

## Configuration Architecture
- **Hierarchical config**: Global → Stage-specific → Environment variable precedence
- **Per-stage LLM configs**: `design_llm`, `devplan_llm`, `handoff_llm` allow different models per pipeline stage
- **Environment override**: Variables like `DESIGN_API_KEY`, `DEVPLAN_MODEL` override global settings
- **Provider resolution**: Automatic API key resolution based on selected provider

## State Management Architecture
- **Checkpoint system**: `.devussy_state/` directory for resumable workflows
- **State persistence**: JSON-based checkpoint files with structured metadata
- **Recovery patterns**: Pipelines can resume from any checkpoint using `resume_from` parameter
- **Cleanup automation**: Automatic checkpoint cleanup with configurable retention

## Integration Architecture
- **Template system**: Automatic template discovery and circular macro support
- **Provider abstraction**: Unified interface across OpenAI, Requesty, Aether, AgentRouter, Generic
- **Repository context**: Analysis results thread through all pipeline stages
- **Git integration**: Optional automatic commits with configurable triggers

## Terminal UI Architecture
- **Textual framework**: Async-first TUI with responsive grid layout
- **Thread separation**: UI runs in background thread to avoid async nesting
- **File encoding**: Always use `encoding='utf-8'` for all file operations to properly handle emojis and Unicode characters
- **Streaming integration**: Real-time token display with phase cancellation support
- **State management**: Phase lifecycle management with full status tracking