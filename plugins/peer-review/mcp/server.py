# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp"]
# ///
"""Transport-only MCP server for the peer-review plugin.

Knows endpoint, auth, request, response, retry, limits. Nothing else: no project
filesystem access, no knowledge of the deliberation protocol, no telemetry, no
disk writes. The command owns the run directory.
"""
import json
import os
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


@mcp.tool()
def peer_profiles() -> dict:
    """List configured challenger profiles with availability. Never returns a key."""
    config, source = _load_profiles()
    profiles = []
    for name, entry in config.get("profiles", {}).items():
        key_env = entry.get("api_key_env", "")
        profiles.append({
            "name": name,
            "base_url": entry.get("base_url", ""),
            "model": entry.get("model", ""),
            "api_key_env": key_env,
            "available": bool(key_env and os.environ.get(key_env)),
        })
    return {"default": config.get("default"), "profiles": profiles, "source": source}


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
    key_env = entry.get("api_key_env", "")
    api_key = os.environ.get(key_env) if key_env else None
    if not api_key:
        return {"error": f"api key environment variable '{key_env or '<unset>'}' is not set; refusing to send"}

    payload: dict = {
        "model": entry["model"],
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
            detail = _redact(error.read().decode("utf-8", "replace")[:500], api_key)
            if error.code in RETRY_STATUSES and attempts == 1:
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue
            return {"error": f"HTTP {error.code} from {url}: {detail}"}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as error:
            return {"error": _redact(f"request failed: {error}", api_key)}


if __name__ == "__main__":
    mcp.run()
