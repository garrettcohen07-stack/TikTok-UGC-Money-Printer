"""
Hook Optimization Agent — generates 3 hook variants and scores them.

Hooks are the first 1-3 seconds of the video — the single most important
element for watch time and completion rate.
"""
from tools.claude_client import HAIKU, SONNET, call_json
from tools.utils import log, new_id, save_hook

_HOOK_SYSTEM = """You are a TikTok hook specialist for a female lifestyle/beauty account.
Your job is to write the most scroll-stopping first line for a TikTok video.

A great TikTok hook:
- Stops someone mid-scroll in the first 0.5 seconds
- Creates instant curiosity or emotional resonance
- Feels like a real person talking, NOT an ad
- Is 10 words or fewer (3 seconds max at natural speech pace)
- Often starts mid-sentence or mid-thought (as if the creator forgot the camera was on)
- Creates a "wait, tell me more" reaction

Hook types that work for female lifestyle/beauty content:
  STATEMENT: Bold claim mid-sentence ("I've been using this every morning for 3 weeks and—")
  CONTRAST:  Unexpected twist ("Everyone told me this was overpriced but actually—")
  STORY:     Personal moment that pulls you in ("I found this completely by accident and—")
  PROBLEM:   Relatable pain point ("My skin has been a nightmare lately and—")
  QUESTION:  Rhetorical that demands answer ("why did nobody tell me about this sooner?")
  REACTION:  Emotional response ("I'm obsessed and I need you to see this")

Score each hook on:
- curiosity (0-10): Does it make you need to keep watching?
- authenticity (0-10): Does it sound like a real person or like marketing?
- retention (0-10): Would you stop scrolling for this?
- tiktok_native (0-10): Does it fit TikTok's style/vibe?

Return a JSON array of exactly 3 hook objects, ordered best-first:
[
  {
    "hook_text": "the hook line",
    "hook_type": "statement|contrast|story|problem|question|reaction",
    "emotion": "curiosity|fomo|aspiration|relatability|problem_solving",
    "scores": {
      "curiosity": 8,
      "authenticity": 9,
      "retention": 7,
      "tiktok_native": 9
    },
    "total_score": 33,
    "why_it_works": "brief explanation"
  }
]

The first hook in the array should be your recommended best option."""


def generate_hooks(
    topic: str,
    script_body: str,
    content_category: str = "bridge",
    brief_angle: str = "",
) -> list[dict]:
    """
    Generate 3 hook variants for a given topic/script.
    Returns list of hook dicts ordered best-first.
    """
    user_prompt = f"""Generate 3 TikTok hooks for this video:

Topic: {topic}
Content category: {content_category}
Creative angle: {brief_angle or "authentic recommendation"}

Script body (for context, NOT the hook itself):
{script_body[:300]}

Write 3 distinct hooks — each using a different hook type.
Return as JSON array."""

    log.info("Generating hooks for: %r", topic)
    hooks = call_json(
        system=_HOOK_SYSTEM,
        user=user_prompt,
        model=SONNET,  # Hooks are critical — use Sonnet
        max_tokens=800,
        temperature=0.9,
    )

    if not isinstance(hooks, list):
        hooks = hooks.get("hooks", [hooks]) if isinstance(hooks, dict) else []

    # Compute total score if not present
    for h in hooks:
        if "total_score" not in h:
            scores = h.get("scores", {})
            h["total_score"] = sum(scores.values())

    # Sort best-first
    hooks.sort(key=lambda h: h.get("total_score", 0), reverse=True)

    log.info("Top hook (score=%d): %r", hooks[0].get("total_score", 0), hooks[0].get("hook_text", ""))
    return hooks


def pick_and_save_best_hook(
    hooks: list[dict],
    content_category: str = "bridge",
) -> dict:
    """Save the best hook to DB and return it with an id."""
    best = hooks[0]
    best["id"] = new_id()
    best["content_category"] = content_category
    save_hook(best)
    return best


def optimize_hooks(
    topic: str,
    script_body: str,
    content_category: str = "bridge",
    brief_angle: str = "",
) -> tuple[dict, list[dict]]:
    """
    Full hook optimization: generate 3 variants, pick best, save to DB.
    Returns (best_hook, all_hooks).
    """
    hooks = generate_hooks(topic, script_body, content_category, brief_angle)
    best = pick_and_save_best_hook(hooks, content_category)
    return best, hooks
