"""Contract-level tests for EventBus/AppContext notifications.

These tests use static analysis of the TypeScript source to ensure that the
core lifecycle events are wired between the window manager, ExecutionView, and
IrcClient as described in appdevplan.md and apphandoff.md.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


RE_EVENT_KEY = re.compile(r"^\s*(\w+):\s*{", re.MULTILINE)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.mark.integration
class TestEventBusContracts:
    """Validate that event keys and emit/subscribe sites stay in sync."""

    def setup_method(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.repo_root = repo_root
        self.event_bus = (
            repo_root
            / "devussy-web"
            / "src"
            / "apps"
            / "eventBus.tsx"
        )
        self.page = (
            repo_root
            / "devussy-web"
            / "src"
            / "app"
            / "page.tsx"
        )
        self.execution_view = (
            repo_root
            / "devussy-web"
            / "src"
            / "components"
            / "pipeline"
            / "ExecutionView.tsx"
        )
        self.irc_client = (
            repo_root
            / "devussy-web"
            / "src"
            / "components"
            / "addons"
            / "irc"
            / "IrcClient.tsx"
        )

    def test_all_typed_events_have_emit_or_subscribe_sites(self) -> None:
        text = _read(self.event_bus)

        # Extract event keys from EventPayloads (excluding the index signature)
        block_start = text.find("type EventPayloads")
        assert block_start != -1, "EventPayloads type missing in eventBus.tsx"

        brace_open = text.find("{", block_start)
        brace_close = text.find("};", brace_open)
        assert brace_open != -1 and brace_close != -1

        block = text[brace_open + 1 : brace_close]
        keys: list[str] = []
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            if line.startswith("["):
                # Skip index signature: [event: string]: any;
                continue
            if ":" in line:
                name = line.split(":", 1)[0].strip()
                keys.append(name)

        assert "planGenerated" in keys
        assert "interviewCompleted" in keys
        assert "designCompleted" in keys
        assert "shareLinkGenerated" in keys
        assert "executionStarted" in keys
        assert "executionCompleted" in keys
        assert "openShareLink" in keys

        # For each event key, verify there is at least one emit/subscribe site
        page_text = _read(self.page)
        exec_text = _read(self.execution_view)
        irc_text = _read(self.irc_client)

        for key in keys:
            # openShareLink is only subscribed to (by page.tsx and emitted from IRC)
            emit_pattern = f"emit('{key}'"
            subscribe_pattern = f"subscribe('{key}'"

            combined = page_text + exec_text + irc_text
            assert (
                emit_pattern in combined or subscribe_pattern in combined
            ), f"No emit/subscribe site found for event '{key}'"

    def test_irc_client_subscribes_and_logs_lifecycle_events(self) -> None:
        text = _read(self.irc_client)

        # Ensure subscriptions exist for key lifecycle events
        assert "bus.subscribe('planGenerated'" in text
        assert "bus.subscribe('interviewCompleted'" in text
        assert "bus.subscribe('designCompleted'" in text
        assert "bus.subscribe('shareLinkGenerated'" in text
        assert "bus.subscribe('executionCompleted'" in text
        assert "bus.subscribe('executionStarted'" in text

        # Core notifications should be mirrored into the Status tab via
        # addSystemMessage, not only sent to the chat channel.
        assert "addSystemMessage(content);" in text

    def test_pipeline_emits_lifecycle_events(self) -> None:
        page_text = _read(self.page)
        exec_text = _read(self.execution_view)

        # Interview/Design/Plan events from the main window manager
        assert "bus.emit('interviewCompleted'" in page_text
        assert "bus.emit('designCompleted'" in page_text
        assert "bus.emit('planGenerated'" in page_text

        # Execution lifecycle events from ExecutionView
        assert "bus.emit('executionStarted'" in exec_text
        assert "bus.emit('executionCompleted'" in exec_text
