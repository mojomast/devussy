"""Integration tests for devussy-web compose/nginx generator.

This test exercises the real `npm run generate:compose` workflow under
`devussy-web/` and asserts that the expected IRC-related services,
proxies, and frontend environment variables are present in the generated
artifacts.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
class TestComposeGenerator:
    """Tests for devussy-web/scripts/generate-compose.ts."""

    def test_generate_compose_creates_expected_files_and_entries(self) -> None:
        """Run `npm run generate:compose` and validate generated artifacts.

        Expectations (derived from apphandoff.md and appdevplan.md):
        - `docker-compose.apps.generated.yml` is created and contains an
          IRC service named `irc_ircd` with the InspIRCd image and
          expected ports/volumes.
        - `nginx/conf.d/apps.generated.conf` is created and contains a
          `/apps/irc/ws/` location proxying to `ircd:8080` with websocket
          settings.
        - The compose overlay includes frontend env vars for the IRC
          client (`NEXT_PUBLIC_IRC_WS_URL`, `NEXT_PUBLIC_IRC_CHANNEL`).
        """

        # Locate repo and devussy-web roots
        repo_root = Path(__file__).resolve().parents[2]
        devussy_web = repo_root / "devussy-web"

        package_json = devussy_web / "package.json"
        if not package_json.exists():
            pytest.skip("devussy-web/package.json not found; frontend not available")

        # Ensure npm is available in the environment
        try:
            subprocess.run(
                ["npm", "--version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            pytest.skip("npm is not available; skipping compose generator test")

        compose_file = devussy_web / "docker-compose.apps.generated.yml"
        nginx_file = devussy_web / "nginx" / "conf.d" / "apps.generated.conf"

        # Run the real generator script via the npm workflow defined in
        # devussy-web/package.json.
        try:
            result = subprocess.run(
                ["npm", "run", "generate:compose"],
                cwd=str(devussy_web),
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            pytest.fail(
                "npm run generate:compose failed with exit code "
                f"{exc.returncode}: {exc.stderr}"
            )

        # Sanity: command should have produced some output
        assert result.stdout or result.stderr

        # Core artifacts should exist
        assert compose_file.exists(), "Expected compose overlay to be generated"
        assert nginx_file.exists(), "Expected nginx apps.generated.conf to be generated"

        compose_content = compose_file.read_text(encoding="utf-8")
        nginx_content = nginx_file.read_text(encoding="utf-8")

        # IRC service metadata from IrcApp.services
        assert "irc_ircd:" in compose_content
        assert "image: inspircd/inspircd-docker:latest" in compose_content
        assert '"6667:6667"' in compose_content
        assert '"8080:8080"' in compose_content
        assert "./irc/conf/inspircd_v2.conf:/inspircd/conf/inspircd.conf" in compose_content
        assert "./irc/logs:/inspircd/logs" in compose_content
        assert "./irc/data:/inspircd/data" in compose_content

        # Frontend env overlay for IRC client
        assert "frontend:" in compose_content
        assert "NEXT_PUBLIC_IRC_WS_URL" in compose_content
        assert "NEXT_PUBLIC_IRC_CHANNEL" in compose_content

        # Nginx proxy metadata from IrcApp.proxy
        assert "/apps/irc/ws/" in nginx_content
        assert "proxy_pass http://ircd:8080/;" in nginx_content
        assert "proxy_http_version 1.1;" in nginx_content
        assert "proxy_set_header Upgrade $http_upgrade;" in nginx_content
        assert "proxy_set_header Connection $connection_upgrade;" in nginx_content


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-v"])
