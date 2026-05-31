"""
Anthropic Claude API client with prompt caching.

Model routing:
  - Sonnet 4.6  (claude-sonnet-4-6)     → creative/nuanced tasks
  - Haiku 4.5   (claude-haiku-4-5-20251001) → classification/simple tasks
"""
import json
from typing import Any, Optional

import anthropic

from tools.utils import log, require_env

# Model IDs
SONNET = "claude-sonnet-4-6"
HAIKU = "claude-haiku-4-5-20251001"

_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=require_env("ANTHROPIC_API_KEY"))
    return _client


def call(
    system: str,
    user: str,
    model: str = SONNET,
    max_tokens: int = 1024,
    cache_system: bool = True,
    temperature: float = 0.7,
) -> str:
    """
    Simple single-turn Claude call. Returns the text response.
    Uses prompt caching on the system prompt by default (saves tokens on repeated calls).
    """
    client = _get_client()

    system_content: list[dict] = [{"type": "text", "text": system}]
    if cache_system:
        system_content[0]["cache_control"] = {"type": "ephemeral"}

    log.debug("Claude call: model=%s max_tokens=%d", model, max_tokens)

    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_content,
        messages=[{"role": "user", "content": user}],
        temperature=temperature,
    )

    usage = msg.usage
    log.debug(
        "Claude usage: input=%d output=%d cache_read=%s cache_write=%s",
        usage.input_tokens,
        usage.output_tokens,
        getattr(usage, "cache_read_input_tokens", "n/a"),
        getattr(usage, "cache_creation_input_tokens", "n/a"),
    )

    return msg.content[0].text


def call_json(
    system: str,
    user: str,
    model: str = SONNET,
    max_tokens: int = 1024,
    cache_system: bool = True,
    temperature: float = 0.7,
) -> Any:
    """
    Call Claude and parse the response as JSON.
    Appends instruction to respond only with valid JSON if not already present.
    """
    if "json" not in user.lower() and "json" not in system.lower():
        user = user + "\n\nRespond with valid JSON only. No markdown, no explanation."

    raw = call(system, user, model, max_tokens, cache_system, temperature)

    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        log.error("Failed to parse Claude JSON response: %s\nRaw: %r", e, raw[:500])
        raise ValueError(f"Claude returned non-JSON: {raw[:200]}") from e
