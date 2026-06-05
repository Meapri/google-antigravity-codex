from __future__ import annotations

import subprocess
from unittest.mock import patch

from google_antigravity_codex import release, writing


def test_writing_routes_to_antigravity_chat():
    seen = {}

    def fake_run_chat(arguments):
        seen.update(arguments)
        return {"text": "Polished text", "usage": {"total_tokens": 3}}

    with patch.object(writing.chat, "run_chat", fake_run_chat):
        result = writing.run_writing(
            {
                "task": "polish",
                "profile": ["chanwoo-ko"],
                "instruction": "Make it natural.",
                "source_text": "rough text",
                "model": "gemini-3.1-pro-high",
            }
        )

    assert result["text"] == "Polished text"
    assert result["task"] == "polish"
    assert result["profiles"] == ["chanwoo-ko"]
    assert seen["model"] == "gemini-3.1-pro-high"
    assert "rough text" in seen["prompt"]


def test_release_snapshot_and_draft_from_git_repo(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
    subprocess.run(["git", "add", "pyproject.toml"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: initial release helper"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    (tmp_path / "README.md").write_text("hello\n", encoding="utf-8")

    snapshot_result = release.release_snapshot({"repo": str(tmp_path)})
    draft_result = release.release_draft({"repo": str(tmp_path), "version": "1.2.4", "tag": "v1.2.4"})

    snapshot = snapshot_result["snapshot"]
    assert snapshot["recommended_bump"] == "minor"
    assert "README.md" in snapshot["changed_files"]
    assert "Release Copilot Draft" in draft_result["text"]
    assert "v1.2.4" in draft_result["text"]
