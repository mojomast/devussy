# Debug Mode Rules (Non-Obvious Only)

## Debug Output Locations
- **Application logs**: `logs/devussy.log` (configurable via `log_file` in config.yaml)
- **Checkpoint state**: `.devussy_state/` directory contains resumable pipeline state
- **Streaming logs**: Optional file logging via `StreamingHandler.create_file_handler()`
- **Test output**: `htmlcov/` directory from coverage reports

## Debug Commands & Tools
- **Verbose mode**: Add `--verbose` flag to any CLI command for detailed logging
- **Debug mode**: Add `--debug` flag for full tracebacks and error details
- **Test debugging**: `pytest --tb=long -v` for detailed test failure output
- **Repository analysis**: `python -m src.cli analyze-repo . --json` for detailed project analysis

## Critical Debug Patterns
- **Async debugging**: Never nest `asyncio.run()` calls - causes event loop conflicts (src/cli.py:3150)
- **Provider switching**: Model selection changes provider automatically - check `config.llm.provider` after model selection
- **Checkpoint resumption**: Use format `<project_name>_pipeline` for consistent checkpoint keys
- **Streaming issues**: Console streaming uses prefixes `[design]`, `[devplan]`, `[handoff]` for identification

## Error Handling Gotchas
- **Silent failures**: Preference loading and streaming setup can fail silently - always check logs
- **File validation**: DevPlan writes fail if anchors missing (`<!-- PROGRESS_LOG_START -->`)
- **API key resolution**: Environment variables override config - check both `DESIGN_API_KEY` and global `OPENAI_API_KEY`
- **Terminal UI**: Textual TUI runs in separate thread - debug UI issues in `src/terminal/terminal_ui.py`

## Performance Debugging
- **Concurrency limits**: Default 5 parallel requests - adjust via `MAX_CONCURRENT_REQUESTS` env var
- **Token limits**: Very high limits (81920+ tokens) for detailed devplan generation
- **Memory leaks**: Streaming handlers use async context managers - ensure proper cleanup
- **State persistence**: Checkpoint system in `.devussy_state/` - verify file permissions

## Repository Analysis Debug
- **Analysis output**: Check `src/interview/repository_analyzer.py` for project type detection logic
- **Code extraction**: `src/interview/code_sample_extractor.py` handles architecture pattern extraction
- **Context threading**: Repository analysis passes through all pipeline stages - verify `repo_analysis` parameter
- **File encoding**: Always use `encoding='utf-8'` for all file operations to properly handle emojis and Unicode characters