"""Lightweight Python entry point for launching Devussy interview.

Usage:
    python -m src.entry

This ensures a Requesty key is present (prompts if missing in 0.1),
then invokes the interactive interview with provider=requesty by default.
"""
from __future__ import annotations

import os
from typing import Optional

from .cli import (
    _load_app_config,
    _resolve_requesty_api_key,
    interactive_design,
)


def main(
    config_path: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    output_dir: Optional[str] = None,
    verbose: bool = False,
) -> None:
    provider = provider or "requesty"
    cfg = _load_app_config(config_path, provider, model, output_dir, verbose)

    # Ensure Requesty key for 0.1
    if (cfg.llm.provider or "").lower() == "requesty":
        _resolve_requesty_api_key(cfg)

    # Run LLM interview flow
    interactive_design(
        config_path=config_path,
        provider=provider,
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
