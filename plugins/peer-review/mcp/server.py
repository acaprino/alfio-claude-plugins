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

# Phrases an OpenAI-compatible endpoint uses when it does not know a parameter we
# send. Matching one downgrades the request shape once, rather than failing a run
# because the endpoint predates the modern field names.
LEGACY_PARAM_HINTS = (
    "max_completion_tokens",
    "stream_options",
    "unsupported_parameter",
    "unsupported parameter",
    "unrecognized request argument",
    "unknown field",
    "extra fields not permitted",
)


def _rejects_modern_params(error_body: str) -> bool:
    low = error_body.lower()
    return any(hint in low for hint in LEGACY_PARAM_HINTS)


def _read_completion(response) -> tuple[str, dict, str | None, str | None]:
    """Read one chat completion, streamed or not.

    Returns (text, usage, model, finish_reason). Server-sent events are the normal
    path; a single JSON body is still accepted, because an endpoint may ignore
    `stream` and answer whole.
    """
    content_type = (response.headers.get("Content-Type") or "").lower()
    if "text/event-stream" not in content_type:
        data = json.loads(response.read().decode("utf-8"))
        choice = data["choices"][0]
        return (
            choice["message"]["content"],
            data.get("usage", {}),
            data.get("model"),
            choice.get("finish_reason"),
        )

    parts: list[str] = []
    usage: dict = {}
    model_name: str | None = None
    finish: str | None = None
    for raw in response:
        line = raw.decode("utf-8", "replace").strip()
        if not line or line.startswith(":") or not line.startswith("data:"):
            continue
        chunk = line[len("data:"):].strip()
        if chunk == "[DONE]":
            break
        try:
            event = json.loads(chunk)
        except json.JSONDecodeError:
            # A malformed chunk is not worth failing the whole round over; the
            # finish_reason and usage checks upstream catch a truncated result.
            continue
        model_name = event.get("model") or model_name
        if event.get("usage"):
            usage = event["usage"]
        for choice in event.get("choices") or []:
            piece = (choice.get("delta") or {}).get("content")
            if piece:
                parts.append(piece)
            if choice.get("finish_reason"):
                finish = choice["finish_reason"]
    return "".join(parts), usage, model_name, finish

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

    tokens = max_output_tokens or entry.get("max_output_tokens")
    # Which field carries the output cap. `max_tokens` is the default because it is
    # the one every OpenAI-compatible endpoint understands, including gateways that
    # normalize it to `max_completion_tokens` on the caller's behalf. Sending the
    # modern field directly is more correct on paper and strictly worse in practice:
    # an endpoint that does not know it drops it SILENTLY, with no error to trigger a
    # fallback, and an ignored cap means an unbounded generation that runs until some
    # proxy times out. Override per profile only for an endpoint that rejects
    # `max_tokens` outright, which reasoning-model APIs do.
    token_param = entry.get("token_param", "max_tokens")
    if token_param not in ("max_tokens", "max_completion_tokens"):
        return {"error": f"profile '{profile}' has invalid token_param '{token_param}'"}

    def _build(legacy: bool) -> bytes:
        """The request body. `legacy` drops fields older endpoints may not know."""
        payload: dict = {
            "model": model,
            "messages": [{"role": "system", "content": system}, *messages],
            # Streamed deliberately. A challenge round is a long generation, and a
            # non-streamed request must complete inside one response, which is what
            # turns a slow answer into a gateway 504. Streaming also converts
            # REQUEST_TIMEOUT_SECONDS from a total-duration cap into an idle cap,
            # since the socket timeout below then applies per chunk read.
            "stream": True,
        }
        if tokens:
            payload["max_tokens" if legacy else token_param] = tokens
        if not legacy:
            # Without this, a streamed response carries no usage block at all, and
            # the verdict's token accounting would silently report nothing.
            payload["stream_options"] = {"include_usage": True}
        if temperature is not None:
            payload["temperature"] = temperature
        return json.dumps(payload).encode("utf-8")

    body = _build(legacy=False)
    if len(body) > MAX_PAYLOAD_BYTES:
        return {"error": f"payload is {len(body)} bytes, over the {MAX_PAYLOAD_BYTES} byte cap; not sent"}

    url = entry["base_url"].rstrip("/") + "/chat/completions"
    retried = False
    downgraded = False
    while True:
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                text, usage, resp_model, finish = _read_completion(response)
            latency_ms = int((time.monotonic() - started) * 1000)
            if finish == "length":
                # A reply cut off at the cap is not a short reply, it is a corrupt
                # one: the round's findings stop mid-list with nothing marking the
                # cut. Refuse it rather than hand the caller a partial challenge.
                return {
                    "error": f"completion truncated at the token cap after {latency_ms} ms "
                    f"(finish_reason=length, {len(text)} chars received); raise "
                    f"max_output_tokens for profile '{profile}' and run again"
                }
            if not text:
                return {"error": f"empty completion after {latency_ms} ms (finish_reason={finish})"}
            result = {
                "text": text,
                "usage": usage,
                "model": resp_model or model,
                "latency_ms": latency_ms,
                "finish_reason": finish,
            }
            # An endpoint that drops the cap does it silently, so the only evidence is
            # spending more than was allowed. Say so: an ignored cap is an unbounded
            # generation, and unbounded generations are what proxies time out on.
            spent = usage.get("completion_tokens")
            if tokens and isinstance(spent, int) and spent > tokens:
                result["warning"] = (
                    f"output cap ignored: asked {tokens} via '{token_param}', spent "
                    f"{spent}. Set token_param on profile '{profile}' to the field this "
                    f"endpoint honors, or the generation runs unbounded"
                )
            return result
        except urllib.error.HTTPError as error:
            error_body = error.read().decode("utf-8", "replace")
            detail = _redact(error_body, api_key)[:500]
            if error.code == 400 and not downgraded and _rejects_modern_params(error_body):
                # Endpoint predates max_completion_tokens / stream_options. Rebuild
                # once in the legacy shape. This does not consume the network retry.
                downgraded = True
                body = _build(legacy=True)
                continue
            if error.code in RETRY_STATUSES and not retried:
                retried = True
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue
            return {"error": f"HTTP {error.code} from {url}: {detail}"}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError) as error:
            return {"error": _redact(f"request failed: {error}", api_key)}


if __name__ == "__main__":
    mcp.run()
