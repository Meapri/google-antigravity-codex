"""Safe interoperability with the official ``agy`` command-line client.

This module never reads the Antigravity system keyring. Authentication remains
owned by the official CLI; readiness is inferred only from public command exit
status and output.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import __version__, security

MIN_SUPPORTED_CLI_VERSION = "1.1.1"
TESTED_CLI_VERSION = "1.1.2"
DEFAULT_TIMEOUT_SECONDS = 300

MODEL_DISPLAY_TO_ID = {
    "Gemini 3.5 Flash (Medium)": "gemini-3.5-flash-medium",
    "Gemini 3.5 Flash (High)": "gemini-3.5-flash-high",
    "Gemini 3.5 Flash (Low)": "gemini-3.5-flash-low",
    "Gemini 3.1 Pro (Low)": "gemini-3.1-pro-low",
    "Gemini 3.1 Pro (High)": "gemini-3.1-pro-high",
    "Claude Sonnet 4.6 (Thinking)": "claude-sonnet-4-6-thinking",
    "Claude Opus 4.6 (Thinking)": "claude-opus-4-6-thinking",
    "GPT-OSS 120B (Medium)": "gpt-oss-120b-medium",
}


class CliError(RuntimeError):
    """Official Antigravity CLI discovery or execution failure."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "agy_cli_error",
        returncode: Optional[int] = None,
        stderr: str = "",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.returncode = returncode
        self.stderr = stderr


@dataclass(frozen=True)
class CliInfo:
    executable: str = ""
    version: str = ""
    installed: bool = False
    compatible: bool = False
    tested: bool = False
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "installed": self.installed,
            "executable": self.executable,
            "version": self.version,
            "minimum_supported_version": MIN_SUPPORTED_CLI_VERSION,
            "tested_version": TESTED_CLI_VERSION,
            "compatible": self.compatible,
            "tested": self.tested,
            "error": self.error,
        }


def _version_tuple(value: str) -> Tuple[int, int, int]:
    match = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", value or "")
    if not match:
        return (0, 0, 0)
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _extract_version(value: str) -> str:
    match = re.search(r"\b(\d+\.\d+\.\d+)\b", value or "")
    return match.group(1) if match else ""


def _sanitize_output(value: str, *, limit: int = 2000) -> str:
    text = str(value or "")
    patterns = (
        (r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+", r"\1<redacted>"),
        (r'(?i)("?(?:access|refresh|id)_token"?\s*[:=]\s*"?)[^"\s&]+', r"\1<redacted>"),
        (r'(?i)("?client_secret"?\s*[:=]\s*"?)[^"\s&]+', r"\1<redacted>"),
        (r"(?i)((?:[?&]|\b)(?:authorization_)?(?:code|token)=)[^&\s]+", r"\1<redacted>"),
    )
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text[: max(0, int(limit))]


def find_executable() -> str:
    override = os.getenv("GOOGLE_ANTIGRAVITY_CLI", "").strip()
    if override:
        candidate = Path(override).expanduser()
        return str(candidate) if candidate.is_file() else ""
    return shutil.which("agy") or ""


def _run(
    command: Sequence[str],
    *,
    timeout: float,
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise CliError(
            f"Antigravity CLI timed out after {timeout:g} seconds.",
            code="agy_cli_timeout",
        ) from exc
    except OSError as exc:
        raise CliError(f"Could not start Antigravity CLI: {exc}", code="agy_cli_unavailable") from exc


def inspect_cli(*, timeout: float = 5.0) -> CliInfo:
    executable = find_executable()
    if not executable:
        return CliInfo(error="agy executable not found")
    try:
        result = _run([executable, "--version"], timeout=timeout)
    except CliError as exc:
        return CliInfo(executable=executable, installed=True, error=str(exc))
    version = _extract_version(f"{result.stdout}\n{result.stderr}")
    if result.returncode != 0 or not version:
        detail = _sanitize_output((result.stderr or result.stdout).strip(), limit=500)
        return CliInfo(
            executable=executable,
            installed=True,
            error=detail[:500] or "could not determine agy version",
        )
    return CliInfo(
        executable=executable,
        version=version,
        installed=True,
        compatible=_version_tuple(version) >= _version_tuple(MIN_SUPPORTED_CLI_VERSION),
        tested=_version_tuple(version) == _version_tuple(TESTED_CLI_VERSION),
    )


def require_cli() -> CliInfo:
    info = inspect_cli()
    if not info.installed:
        raise CliError(
            "Official Antigravity CLI (agy) is not installed or GOOGLE_ANTIGRAVITY_CLI is invalid.",
            code="agy_cli_unavailable",
        )
    if not info.version:
        raise CliError(info.error or "Could not determine agy version.", code="agy_cli_version_unknown")
    if not info.compatible:
        raise CliError(
            f"Antigravity CLI {info.version} is older than the supported minimum "
            f"{MIN_SUPPORTED_CLI_VERSION}.",
            code="agy_cli_unsupported",
        )
    return info


def list_models(*, timeout: float = 30.0) -> List[Dict[str, str]]:
    info = require_cli()
    result = _run([info.executable, "models"], timeout=timeout)
    if result.returncode != 0:
        detail = _sanitize_output((result.stderr or result.stdout).strip())
        raise CliError(
            f"Antigravity CLI model listing failed: {detail or 'unknown error'}",
            code="agy_cli_models_failed",
            returncode=result.returncode,
            stderr=result.stderr,
        )
    models: List[Dict[str, str]] = []
    for raw_line in result.stdout.splitlines():
        display_name = raw_line.strip()
        if not display_name:
            continue
        models.append(
            {
                "id": MODEL_DISPLAY_TO_ID.get(display_name, display_name),
                "display_name": display_name,
                "source": "agy models",
            }
        )
    return models


def run_prompt(arguments: Dict[str, Any]) -> Dict[str, Any]:
    prompt = str(arguments.get("prompt") or "").strip()
    if not prompt:
        raise CliError("prompt is required", code="agy_cli_prompt_missing")
    if len(prompt.encode("utf-8")) > 128 * 1024:
        raise CliError("prompt exceeds the 128 KiB limit", code="agy_cli_prompt_too_large")
    if not security.cli_bridge_enabled():
        raise CliError(
            "The Codex-to-agy chat bridge is disabled by default. Google's Antigravity terms "
            "restrict third-party access using Antigravity login. Enable "
            "GOOGLE_ANTIGRAVITY_ENABLE_CLI_BRIDGE=1 only after confirming your applicable agreement.",
            code="agy_cli_bridge_disabled",
        )
    if int(os.getenv("GOOGLE_ANTIGRAVITY_CLI_BRIDGE_DEPTH", "0") or 0) >= 1:
        raise CliError(
            "Blocked recursive agy -> MCP -> agy invocation.",
            code="agy_cli_recursion_blocked",
        )
    mode = str(arguments.get("mode") or "plan").strip() or "plan"
    if mode not in {"plan", "accept-edits"}:
        raise CliError(f"unsupported agy mode: {mode}", code="agy_cli_mode_invalid")
    if mode == "accept-edits" and not security.env_flag("GOOGLE_ANTIGRAVITY_ALLOW_MUTATING_CLI"):
        raise CliError(
            "accept-edits mode is blocked; set GOOGLE_ANTIGRAVITY_ALLOW_MUTATING_CLI=1 locally to opt in.",
            code="agy_cli_mutation_blocked",
        )
    info = require_cli()
    command = [info.executable, "--print", prompt]
    model = str(arguments.get("model") or "").strip()
    agent = str(arguments.get("agent") or "").strip()
    if model:
        command.extend(["--model", model])
    if agent:
        command.extend(["--agent", agent])
    if mode:
        command.extend(["--mode", mode])
    sandbox = bool(arguments.get("sandbox", True))
    if not sandbox and not security.env_flag("GOOGLE_ANTIGRAVITY_ALLOW_UNSANDBOXED_CLI"):
        raise CliError(
            "Unsandboxed CLI execution is blocked.",
            code="agy_cli_unsandboxed_blocked",
        )
    if sandbox:
        command.append("--sandbox")
    timeout = float(arguments.get("timeout_sec") or DEFAULT_TIMEOUT_SECONDS)
    if not math.isfinite(timeout):
        raise CliError("timeout_sec must be finite", code="agy_cli_timeout_invalid")
    timeout = max(20.0, min(timeout, 1800.0))
    command.extend(["--print-timeout", f"{timeout:g}s"])
    cwd_raw = str(arguments.get("cwd") or "").strip()
    try:
        cwd = (
            security.resolve_allowed_path(cwd_raw, purpose="agy cwd", directory=True)
            if cwd_raw
            else None
        )
    except ValueError as exc:
        raise CliError(str(exc), code="agy_cli_cwd_invalid") from exc

    child_env = dict(os.environ)
    child_env["GOOGLE_ANTIGRAVITY_CLI_BRIDGE_DEPTH"] = "1"
    result = _run(command, timeout=max(25.0, timeout + 5.0), cwd=cwd, env=child_env)
    text = result.stdout.strip()
    if result.returncode != 0:
        detail = _sanitize_output(result.stderr.strip() or text)
        raise CliError(
            f"Antigravity CLI request failed: {detail or 'unknown error'}",
            code="agy_cli_request_failed",
            returncode=result.returncode,
            stderr=result.stderr,
        )
    if not text:
        raise CliError(
            "Antigravity CLI returned an empty response.",
            code="agy_cli_empty_response",
            returncode=result.returncode,
        )
    return {
        "success": True,
        "text": text,
        "provider": "google-antigravity",
        "backend": "agy-cli",
        "model": model,
        "warnings": [],
        "diagnostics": {
            "cli_version": info.version,
            "tested_cli_version": TESTED_CLI_VERSION,
            "agent": agent,
            "mode": mode,
            "sandbox": sandbox,
            "returncode": result.returncode,
        },
    }


def plugin_root() -> Path:
    return Path(__file__).resolve().parent.parent


def validate_plugin(*, root: Optional[Path] = None, timeout: float = 30.0) -> Dict[str, Any]:
    target = (root or plugin_root()).resolve()
    info = require_cli()
    result = _run([info.executable, "plugin", "validate", str(target)], timeout=timeout)
    output = _sanitize_output((result.stdout or result.stderr).strip())
    return {
        "valid": result.returncode == 0,
        "returncode": result.returncode,
        "output": output[:2000],
        "plugin_root": str(target),
    }


def status(_: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    info = inspect_cli()
    root = plugin_root()
    models: List[Dict[str, str]] = []
    model_error = ""
    validation: Dict[str, Any] = {
        "valid": False,
        "returncode": None,
        "output": "agy is unavailable",
        "plugin_root": str(root),
    }
    if info.compatible:
        try:
            models = list_models()
        except CliError as exc:
            model_error = str(exc)
        try:
            validation = validate_plugin(root=root)
        except CliError as exc:
            validation["output"] = str(exc)
    model_listing_ready = bool(models)
    warnings: List[str] = []
    if info.installed and info.compatible and not info.tested:
        warnings.append("agy_version_not_exactly_tested")
    if model_error:
        warnings.append("agy_session_or_model_check_failed")
    if not validation.get("valid"):
        warnings.append("agy_plugin_validation_failed")
    return {
        "success": info.installed and info.compatible and bool(validation.get("valid")),
        "text": (
            f"agy {info.version or 'unavailable'}; "
            f"plugin {'valid' if validation.get('valid') else 'invalid'}; "
            f"model listing {'ready' if model_listing_ready else 'unavailable'}"
        ),
        "provider": "google-antigravity",
        "backend": "agy-cli",
        "plugin_version": __version__,
        "cli": info.to_dict(),
        "native_plugin": validation,
        "model_listing_ready": model_listing_ready,
        "authentication_state": "not_directly_inspectable",
        "authentication_note": (
            "agy has no non-interactive auth-status command. The optional cli_chat bridge is "
            "disabled by default; review the applicable Antigravity terms before enabling it."
        ),
        "model_count": len(models),
        "models": models,
        "model_error": model_error,
        "keyring_read_by_plugin": False,
        "authentication_owner": "agy",
        "config_paths": {
            "settings": str(Path.home() / ".gemini" / "antigravity-cli" / "settings.json"),
            "plugins": str(Path.home() / ".gemini" / "config" / "plugins"),
            "shared_config": str(Path.home() / ".gemini" / "config"),
        },
        "warnings": warnings,
        "diagnostics": {"tested_cli_version": TESTED_CLI_VERSION},
    }
