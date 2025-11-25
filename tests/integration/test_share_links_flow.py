"""Integration tests for share link helpers and `/share` route wiring.

These tests validate the behaviour of `devussy-web/src/shareLinks.ts` and the
Next.js `/share` page at a contract level using Python + Node/ts-node.
"""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
from pathlib import Path

import pytest


def _require_node() -> None:
  """Skip tests if Node.js tooling is not available.

  We rely on `npx ts-node` and the devussy-web TypeScript config; if Node or
  npx/ts-node are missing, these tests are skipped rather than failing.
  """

  if shutil.which("node") is None and shutil.which("node.exe") is None:
      pytest.skip("Node.js is not available on PATH")

  # Lightweight check that npx works; ignore failures from missing project deps
  if shutil.which("npx") is None and shutil.which("npx.cmd") is None:
      pytest.skip("npx is not available on PATH")


def _run_share_links_harness(args: list[str]) -> str:
    """Run the TypeScript shareLinks harness and return stdout.

    The harness lives at `devussy-web/scripts/src/shareLinks_harness.ts` and is
    executed via ts-node using the same tsconfig.scripts.json that powers the
    compose generator.
    """

    repo_root = Path(__file__).resolve().parents[2]
    devussy_web = repo_root / "devussy-web"

    harness = devussy_web / "scripts" / "src" / "shareLinks_harness.ts"
    if not harness.exists():
        pytest.skip("shareLinks_harness.ts not found; frontend harness missing")

    _require_node()

    cmd = [
        "npx",
        "ts-node",
        "-r",
        "tsconfig-paths/register",
        "--project",
        "tsconfig.scripts.json",
        str(harness.relative_to(devussy_web)),
        *args,
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(devussy_web),
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        # On some Windows environments, npx/ts-node may not be discoverable
        # even if Node is installed. In that case we treat the harness as
        # unavailable rather than failing the suite.
        pytest.skip("Node.js shareLinks harness (npx/ts-node) is not available on PATH")
    except subprocess.CalledProcessError as exc:
        pytest.fail(
            "shareLinks harness failed with exit code "
            f"{exc.returncode}: {exc.stderr}"
        )

    return result.stdout.strip()


@pytest.mark.integration
class TestShareLinksRoundTrip:
    """Round-trip tests for generateShareLink/decodeSharePayload."""

    def test_generate_and_decode_share_link_roundtrip_design(self) -> None:
        """Valid design payload survives encode/decode via TS helpers.

        This calls the real TypeScript implementation under Node (server-side
        path: relative `/share?payload=...` URLs) and asserts that stage and
        projectName are preserved.
        """

        payload = {
            "projectName": "Test Project",
            "requirements": "Build a simple web API",
            "languages": ["Python", "TypeScript"],
        }

        out_raw = _run_share_links_harness([
            "roundtrip",
            "design",
            json.dumps(payload),
        ])
        out = json.loads(out_raw)

        url = out["url"]
        encoded = out["encoded"]
        decoded = out["decoded"]

        # Server-side path should be relative
        assert url.startswith("/share?payload=")
        assert isinstance(encoded, str) and encoded

        assert decoded["stage"] == "design"
        assert decoded["data"]["projectName"] == "Test Project"
        assert decoded["data"]["requirements"] == "Build a simple web API"

    def test_decode_invalid_payload_returns_null(self) -> None:
        """Malformed payloads decode to null in TS helper.

        Mirrors the defensive behaviour described in appdevplan.md and
        apphandoff.md: invalid base64 or structurally invalid JSON should not
        throw but simply return `null`.
        """

        out_raw = _run_share_links_harness(["decode", "not-base64"])
        decoded = json.loads(out_raw)
        assert decoded is None

    def test_decode_payload_missing_stage_returns_null(self) -> None:
        """Base64 payloads without a stage field are rejected.

        We craft a base64-url string that encodes an object with only `data`
        and confirm that the TS helper returns `null`.
        """

        obj = {"data": {"projectName": "No Stage"}}
        json_bytes = json.dumps(obj).encode("utf-8")
        b64 = base64.b64encode(json_bytes).decode("ascii")
        # Convert to URL-safe variant compatible with shareLinks.ts
        b64url = b64.replace("+", "-").replace("/", "_").rstrip("=")

        out_raw = _run_share_links_harness(["decode", b64url])
        decoded = json.loads(out_raw)
        assert decoded is None


@pytest.mark.integration
class TestShareRouteWiring:
    """Static checks for the `/share` page wiring.

    These do not execute React code but assert that the route uses the
    shareLinks helpers and persists payloads into sessionStorage as per the
    design.
    """

    def test_share_page_uses_decode_and_session_storage(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        share_page = (
            repo_root
            / "devussy-web"
            / "src"
            / "app"
            / "share"
            / "page.tsx"
        )
        text = share_page.read_text(encoding="utf-8")

        assert "decodeSharePayload" in text
        assert "devussy_share_payload" in text
        assert "sessionStorage.setItem('devussy_share_payload'" in text
        assert "This link contains shared Devussy state" in text
        assert "Open Devussy" in text
