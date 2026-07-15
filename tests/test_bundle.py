from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent


def test_bundle_is_allowlisted_and_platform_aware(tmp_path):
    posix = tmp_path / "posix"
    windows = tmp_path / "windows"
    script = ROOT / "scripts" / "build_plugin_bundle.py"

    subprocess.run(
        [sys.executable, str(script), "--output", str(posix), "--platform", "posix"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [sys.executable, str(script), "--output", str(windows), "--platform", "windows"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    relative_files = {path.relative_to(posix).as_posix() for path in posix.rglob("*") if path.is_file()}
    assert "plugin.json" in relative_files
    assert "google_antigravity_codex/mcp_server.py" in relative_files
    assert not any(part in {".git", ".pytest_cache", ".ruff_cache", "tests", "build"} for path in relative_files for part in Path(path).parts)

    posix_config = json.loads((posix / "mcp_config.json").read_text(encoding="utf-8"))
    windows_config = json.loads((windows / "mcp_config.json").read_text(encoding="utf-8"))
    assert posix_config["mcpServers"]["google-antigravity-codex"]["command"] == "python3"
    assert windows_config["mcpServers"]["google-antigravity-codex"]["command"] == "py"
    assert windows_config["mcpServers"]["google-antigravity-codex"]["args"][0] == "-3"
    server = posix_config["mcpServers"]["google-antigravity-codex"]
    assert server["env"]["GOOGLE_ANTIGRAVITY_RUNNING_UNDER_AGY"] == "1"
    assert "google_antigravity_cli_chat" in server["disabledTools"]
    assert "google_antigravity_chat" not in server["disabledTools"]
    assert "google_antigravity_generate_image" not in server["disabledTools"]
