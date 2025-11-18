"""
UI tokens mapping and helpers to render terminal-friendly emoji output.

This module centralizes emoji replacements. Use `render(text)` where
print/echo output is intended for the user-facing terminal UI.
"""
from __future__ import annotations

from typing import Dict

# Minimal set used by the CLI/interactive outputs. Keep this small; add
# entries as needed to standardize the look-and-feel.
TOKENS: Dict[str, str] = {
    "[ROCKET]": "🚀",
    "[OK]": "✅",
    "[ERROR]": "❌",
    "[WARN]": "⚠️",
    "[FOLDER]": "📁",
    "[FILE]": "📄",
    "[SAVE]": "💾",
    "[LIST]": "📋",
    "[NOTE]": "📝",
    "[WAIT]": "⏳",
    "[SEND]": "📤",
    "[REFRESH]": "🔄",
    "[BOOKMARK]": "📦",
    "[FAST]": "⚡",
    "[TARGET]": "🎯",
    "[STATS]": "📊",
    "[SCRIPT]": "🧭",
    "[ROBOT]": "🤖",
    "[ROBOT_MUSIC]": "🎵",
    "[DASHBOARD]": "📊",
    "[PLAN]": "🗺️",
    "[BROOM]": "🧹",
}


def render(text: str) -> str:
    """Return text with placeholders replaced by emoji.

    This is designed for terminal UI output and leaves everything else untouched.
    """
    if not text or "[" not in text:
        return text
    rendered = text
    for token, emoji in TOKENS.items():
        rendered = rendered.replace(token, emoji)
    return rendered
