"""Template loading and rendering using Jinja2."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template


def _templates_dir() -> Path:
    # Resolve the project root as the parent of this file's directory
    return Path(__file__).resolve().parents[1] / "templates"


@lru_cache(maxsize=1)
def _env() -> Environment:
    loader = FileSystemLoader(str(_templates_dir()))
    env = Environment(
        loader=loader, autoescape=False, trim_blocks=True, lstrip_blocks=True
    )
    # Add Python builtins to Jinja2 environment
    env.globals["enumerate"] = enumerate
    env.globals["len"] = len
    return env


def load_template(name: str) -> Template:
    """Load a template by relative name from the templates directory."""
    tpl = _env().get_template(name)
    return tpl


def render_template(name: str, context: dict[str, Any]) -> str:
    """Render the named template with provided context."""
    return load_template(name).render(**context)
