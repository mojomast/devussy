"""Lightweight Python entry point for launching Devussy interview.

Usage:
    python -m src.entry

This entrypoint:
- Respects provider/model configuration from config.yaml and environment (e.g. .env).
- Only applies Requesty-specific behavior when Requesty is actually selected.
"""
from __future__ import annotations

import os
from typing import Optional

from .cli import (
    _load_app_config,
    _resolve_requesty_api_key,
    interactive_design,
    _render_splash,
)


def main(
    config_path: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    output_dir: Optional[str] = None,
    verbose: bool = False,
) -> None:
    # Show the same splash as the CLI unless disabled via env
    try:
        env_off = os.getenv("DEVUSSY_NO_SPLASH", "").strip().lower() in {"1", "true", "yes"}
        if not env_off:
            _render_splash()
    except Exception:
        # Never fail due to splash
        pass

    # Let _load_app_config resolve provider/model from config/.env unless explicitly overridden.
    # Ensure UI preferences are loaded during startup
    cfg = _load_app_config(config_path, provider, model, output_dir, verbose)

    # If the resolved provider is Requesty, ensure its API key is available.
    resolved_provider = (cfg.llm.provider or "").lower()
    if resolved_provider == "requesty":
        _resolve_requesty_api_key(cfg)

    # Run LLM interview flow using the resolved provider.
    # Passing cfg.llm.provider ensures python -m src.entry behaves like the CLI launch command.
    interactive_design(
        config_path=config_path,
        provider=cfg.llm.provider,
        model=model,
        output_dir=output_dir,
        temperature=None,
        max_tokens=None,
        select_model=False,
        save_session=None,
        resume_session=None,
        llm_interview=True,
        scripted=False,
        streaming=False,
        verbose=verbose,
        debug=False,
    )


if __name__ == "__main__":
    main()
