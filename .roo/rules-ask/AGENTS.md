# Ask Mode Rules (Non-Obvious Only)

## Documentation Structure
- **Main AGENTS.md**: Project-level guidance in root directory
- **Mode-specific rules**: `.roo/rules-{mode}/AGENTS.md` files for specialized guidance
- **Configuration docs**: `config/config.yaml` contains comprehensive LLM provider configurations
- **Pipeline templates**: `templates/*.jinja` for document generation with circular macro support

## Non-Obvious Documentation Context
- **Interview questionnaires**: `config/questions.yaml` contains scripted question flows
- **Provider examples**: `src/clients/` directory contains canonical implementation examples (not just docs)
- **Template system**: Uses Jinja2 with circular macro support from `templates/_circular_macros.jinja`
- **Template usage**: Templates are auto-discovered and used for document generation
- **Documentation generation**: Built-in support for creating documentation with citations and timestamps

## Code Organization Insights
- **"src/" vs expected structure**: Contains CLI framework, not web application source
- **Provider implementations**: Each LLM provider (OpenAI, Requesty, Aether, etc.) in `src/clients/`
- **Pipeline stages**: Design → Basic DevPlan → Detailed DevPlan → Handoff (documented in README)
- **Repository analysis**: `src/interview/` contains codebase analysis for context-aware questioning

## API Integration Documentation
- **Multiple providers**: OpenAI, Requesty, Aether, AgentRouter, Generic OpenAI-compatible
- **Provider switching**: Model selection automatically switches active provider
- **Per-stage configs**: Different models can be used for design/devplan/handoff stages
- **Environment precedence**: `DESIGN_API_KEY`, `DEVPLAN_MODEL` override global settings per stage

## File Management Documentation
- **Safe writes**: `src/file_manager.py:47` - `safe_write_devplan()` with .bak files and validation
- **Anchor requirements**: DevPlan files must contain `<!-- PROGRESS_LOG_START -->` anchors
- **Template integration**: Automatic template discovery and content generation
- **Checkpoint system**: Resumable workflows stored in `.devussy_state/`

## Streaming & UI Documentation
- **Console streaming**: Real-time token display with prefixes like `[design]`, `[devplan]`
- **Terminal UI**: Textual-based interface for phase management
- **Interactive modes**: Single-window streaming vs traditional interview flow
- **File encoding**: Always use `encoding='utf-8'` for all file operations to properly handle emojis and Unicode characters
- **Provider integration**: All LLM providers support real-time streaming