# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp>=2.0.0,<3"]
# ///
"""Transport-only MCP server for the peer-review plugin.

Knows endpoint, auth, request, response, retry, limits. Nothing else: no project
filesystem access, no knowledge of the deliberation protocol, no telemetry, no
disk writes. The command owns the run directory.
"""
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from mcp.server.mcpserver import MCPServer as FastMCP

MAX_PAYLOAD_BYTES = 400_000
REQUEST_TIMEOUT_SECONDS = 180
RETRY_STATUSES = {429, 500, 502, 503, 504}
RETRY_BACKOFF_SECONDS = 5

mcp = FastMCP("peer-review")


def _profile_locations() -> list[Path]:
    locations = []
    env_path = os.environ.get("PEER_REVIEW_PROFILES")
    if env_path:
        locations.append(Path(env_path))
    locations.append(Path.cwd() / ".peer-review" / "profiles.json")
    locations.append(Path.home() / ".peer-review" / "profiles.json")
    return locations


def _load_profiles() -> tuple[dict, str | None]:
    for path in _profile_locations():
        if path.is_file():
            with path.open(encoding="utf-8") as handle:
                return json.load(handle), str(path)
    return {"default": None, "profiles": {}}, None


def _redact(text: str, secret: str | None) -> str:
    return text.replace(secret, "<redacted>") if secret else text


ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

MALFORMED_ENV_HINT = (
    "api_key_env must hold the NAME of an environment variable, not a key. "
    "Put a literal key in the 'api_key' field instead. The offending value is "
    "deliberately not echoed: if it is the key, it is a secret."
)


def _resolve_key(entry: dict) -> tuple[str | None, str, list[str]]:
    """Resolve a profile's API key.

    Returns (key, key_source, warnings). Never returns the offending value of a
    malformed api_key_env: in that situation the value is itself the secret.

    Order: api_key_env when the named variable is set, then the literal api_key.
    The environment wins so a machine can override the file without editing it.
    """
    raw_env = entry.get("api_key_env") or ""
    literal = entry.get("api_key") or ""
    warnings: list[str] = []

    malformed = bool(raw_env) and not ENV_NAME.match(raw_env)
    if malformed:
        warnings.append(MALFORMED_ENV_HINT)
        raw_env = ""

    if raw_env:
        from_env = os.environ.get(raw_env)
        if from_env:
            return from_env, "env", warnings
        warnings.append(f"environment variable '{raw_env}' is not set")

    if literal:
        return literal, "literal", warnings

    return None, "malformed_env_name" if malformed else "none", warnings


def _git_ignored(path: Path) -> bool | None:
    """Whether git ignores path. None when git cannot decide (no repo, no git)."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(path)],
            cwd=str(path.parent),
            capture_output=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


@mcp.tool()
def peer_profiles() -> dict:
    """List configured challenger profiles with availability. Never returns a key."""
    config, source = _load_profiles()
    profiles = []
    any_literal = False
    for name, entry in config.get("profiles", {}).items():
        key, key_source, warnings = _resolve_key(entry)
        any_literal = any_literal or key_source == "literal"
        profiles.append({
            "name": name,
            "base_url": entry.get("base_url", ""),
            "model": entry.get("model", ""),
            "api_key_env": entry.get("api_key_env", "") if ENV_NAME.match(entry.get("api_key_env", "") or "") else "",
            "key_source": key_source,
            "warnings": warnings,
            "available": bool(key),
        })

    result = {"default": config.get("default"), "profiles": profiles, "source": source}
    if any_literal and source and _git_ignored(Path(source)) is False:
        result["warning"] = (
            f"{source} holds a literal api_key and is NOT ignored by git. Move it to "
            "~/.peer-review/profiles.json, or add it to .gitignore, before committing."
        )
    return result


@mcp.tool()
def peer_ask(
    profile: str,
    system: str,
    messages: list[dict],
    max_output_tokens: int | None = None,
    temperature: float | None = None,
) -> dict:
    """Send one request to the named profile's OpenAI-compatible endpoint."""
    config, _ = _load_profiles()
    entry = config.get("profiles", {}).get(profile)
    if entry is None:
        known = ", ".join(sorted(config.get("profiles", {}))) or "none configured"
        return {"error": f"unknown profile '{profile}' (known: {known})"}
    api_key, key_source, warnings = _resolve_key(entry)
    if not api_key:
        reason = "; ".join(warnings) if warnings else (
            f"profile '{profile}' configures neither 'api_key_env' nor 'api_key'"
        )
        return {"error": f"no api key resolved ({key_source}): {reason}; refusing to send"}

    model = entry.get("model")
    if not model:
        return {"error": f"profile '{profile}' is missing required field 'model'"}

    payload: dict = {
        "model": model,
        "messages": [{"role": "system", "content": system}, *messages],
    }
    tokens = max_output_tokens or entry.get("max_output_tokens")
    if tokens:
        payload["max_tokens"] = tokens
    if temperature is not None:
        payload["temperature"] = temperature
    body = json.dumps(payload).encode("utf-8")
    if len(body) > MAX_PAYLOAD_BYTES:
        return {"error": f"payload is {len(body)} bytes, over the {MAX_PAYLOAD_BYTES} byte cap; not sent"}

    url = entry["base_url"].rstrip("/") + "/chat/completions"
    attempts = 0
    while True:
        attempts += 1
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                data = json.loads(response.read().decode("utf-8"))
            latency_ms = int((time.monotonic() - started) * 1000)
            return {
                "text": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data.get("model", entry["model"]),
                "latency_ms": latency_ms,
            }
        except urllib.error.HTTPError as error:
            # Never rebind `body`: it is the request payload and the retry below resends it.
            error_body = error.read().decode("utf-8", "replace")
            detail = _redact(error_body, api_key)[:500]
            if error.code in RETRY_STATUSES and attempts == 1:
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue
            return {"error": f"HTTP {error.code} from {url}: {detail}"}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError) as error:
            return {"error": _redact(f"request failed: {error}", api_key)}


if __name__ == "__main__":
    mcp.run()
