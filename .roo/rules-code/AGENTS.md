# Code Mode Rules (Non-Obvious Only)

## Custom Utilities (Project-Specific)
- **File writing**: Always use `src/file_manager.py:47` - `safe_write_devplan()` instead of direct file writes. It creates `.bak` files and validates content invariants
- **Streaming**: Use `src/streaming.py:152` - `StreamingHandler.create_console_handler()` for real-time token display with prefixes
- **Config loading**: Call `src/config.py:254` - `load_config()` which merges YAML + environment variables with specific precedence rules
- **LLM clients**: Use `src/clients/factory.py:create_llm_client()` to properly initialize provider-specific clients

## Async Patterns (Critical)
- **Never nest**: Never use `asyncio.run()` inside async functions (src/cli.py line ~3150) - causes event loop conflicts
- **Thread integration**: Terminal UI (Textual) runs in background thread to avoid async nesting issues (src/terminal/terminal_ui.py)
- **Streaming callbacks**: Use synchronous token callbacks in generators to avoid coroutine warnings

## Required Import Patterns
- **Future annotations**: Always start files with `from __future__ import annotations` for forward references
- **Logger pattern**: Use `from .logger import get_logger` and `logger = get_logger(__name__)` pattern consistently
- **Pydantic models**: All data models inherit from `pydantic.BaseModel` with proper validation

## File Validation Requirements
- **DevPlan files**: Must contain `<!-- PROGRESS_LOG_START -->` and `<!-- NEXT_TASK_GROUP_START -->` anchors or writes fail (src/file_manager.py:41-44)
- **Template usage**: Templates use Jinja2 with circular macro support from `templates/_circular_macros.jinja`
- **State management**: Checkpoint files use specific format `<project_name>_pipeline` (src/cli.py line ~1210)

## Critical Provider Patterns
- **Model switching**: LLM model selection automatically switches provider - don't assume provider remains constant
- **API keys**: Environment variables like `DESIGN_API_KEY`, `DEVPLAN_MODEL` override global settings per stage (src/config.py line ~365)
- **Client initialization**: Each provider has specific initialization requirements (src/clients/)

## Error Handling Patterns
- **Graceful degradation**: Never crash on optional features - always provide fallback paths
- **Silent failures**: Some operations fail silently (streaming setup, preference loading) - always wrap in try/catch
- **Validation first**: File operations validate content invariants before writing (src/file_manager.py:68)
- **File encoding**: Always use `encoding='utf-8'` for all file operations to properly handle emojis and Unicode characters