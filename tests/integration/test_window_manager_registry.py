"""Tests for window manager & AppRegistry invariants.

These are structural tests that ensure the window manager in
`devussy-web/src/app/page.tsx` stays aligned with `AppRegistry` and that
single-instance apps are correctly marked.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.mark.integration
class TestWindowManagerRegistryInvariants:
    def setup_method(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.repo_root = repo_root
        self.page = repo_root / "devussy-web" / "src" / "app" / "page.tsx"
        self.registry = repo_root / "devussy-web" / "src" / "apps" / "AppRegistry.ts"
        self.help_app = repo_root / "devussy-web" / "src" / "apps" / "help.tsx"
        self.irc_app = repo_root / "devussy-web" / "src" / "apps" / "irc.tsx"
        self.model_settings_app = (
            repo_root
            / "devussy-web"
            / "src"
            / "apps"
            / "modelSettings.tsx"
        )

    def test_window_type_comes_from_app_registry(self) -> None:
        text = _read(self.page)
        assert "type WindowType = keyof typeof AppRegistry;" in text

    def test_app_registry_includes_expected_apps(self) -> None:
        text = _read(self.registry)

        # Ensure the core pipeline and utility apps are present
        for app_id in [
            "init",
            "interview",
            "design",
            "plan",
            "execute",
            "handoff",
            "help",
            "model-settings",
            "pipeline",
            "irc",
        ]:
            assert (
                f'"{app_id}"' in text or f"{app_id}" in text
            ), f"Expected app id '{app_id}' to appear in AppRegistry.ts"

    def test_single_instance_flags_for_help_irc_model_settings(self) -> None:
        help_text = _read(self.help_app)
        irc_text = _read(self.irc_app)
        model_text = _read(self.model_settings_app)

        assert "singleInstance: true" in help_text
        assert "singleInstance: true" in irc_text
        assert "singleInstance: true" in model_text

    def test_taskbar_uses_on_open_app_handler(self) -> None:
        """Ensure Taskbar is driven by generic onOpenApp handler.

        This confirms that the Start menu and taskbar now rely on app IDs from
        the registry instead of bespoke handlers for Help/IRC/Model Settings.
        """

        text = _read(self.page)

        assert "<Taskbar" in text
        assert "onOpenApp={(appId)" in text
        assert "spawnAppWindow(appId as WindowType, appDef.name);" in text
