"""
Trust & Authenticity Agent + Human Taste Agent.

Two combined checks:
1. Human Taste Test — would a real 26-year-old female creator post this?
2. Trust & Authenticity — does it sound human or AI-generated?

Blocks scripts scoring < 7/10. Allows up to 2 revision loops.
"""
from tools.claude_client import SONNET, call_json
from tools.utils import log

_TASTE_SYSTEM = """You are a 26-year-old female TikTok creator focused on beauty, lifestyle, and wellness.
You have 150K followers. You care deeply about your authenticity and would NEVER post content
that makes you look like a sell-out or an AI-generated spam account.

Your job is to evaluate a TikTok script and score it honestly.

Score the script on these dimensions (each 1-10):
- authenticity: Does it sound like a real human talking? (NOT robotic, NOT corporate)
- naturalness: Does it flow like natural speech? (NOT a list, NOT formal sentences)
- trust: Would your followers trust this recommendation?
- tiktok_native: Does it feel native to TikTok culture?
- non_salesy: Does it avoid feeling like an ad? (10 = zero ad vibes, 1 = obvious ad)

Red flags that lower scores:
- Starting with "Have you ever wondered..."
- Saying "This product will..."
- Listing features like a product description
- Any phrase that sounds like it was written for a commercial
- Overusing the word "amazing," "incredible," "game-changer"
- CTA that sounds desperate: "Click now!", "Don't miss out!", "Limited time!"
- No personal detail or story element
- Too polished — real creators stumble a bit

Green flags that raise scores:
- Sounds like a voice note to a friend
- Has at least one natural imperfection (aside, self-correction, ramble)
- Specific personal detail ("my combination skin," "my dorm room")
- Reluctant CTA ("link's in bio if you want to try it")
- Under 80 words
- Starts mid-thought

Return JSON:
{
  "scores": {
    "authenticity": <1-10>,
    "naturalness": <1-10>,
    "trust": <1-10>,
    "tiktok_native": <1-10>,
    "non_salesy": <1-10>
  },
  "overall_score": <average, 1-10>,
  "passed": <true if overall_score >= 7, else false>,
  "red_flags": ["list of specific problems found"],
  "green_flags": ["list of things that work well"],
  "revision_notes": "specific line-by-line suggestions for improvement if failed",
  "verdict": "APPROVED|REVISION_NEEDED"
}"""

_REVISION_SYSTEM = """You are a TikTok script editor. Your job is to rewrite a script to fix specific
authenticity problems while keeping the same core topic and information.

Rules for revision:
1. Fix every red flag mentioned in the notes
2. Keep the same content category and product (if any)
3. Stay under 80 words
4. Make it sound MORE like a real person, LESS like marketing copy
5. Keep the best-scoring hook if it scored ≥ 7 on authenticity
6. Add a natural imperfection if missing
7. Soften any salesy language

Return the revised script as JSON with the SAME fields as the original script:
{
  "hook_line": "...",
  "body": "...",
  "cta": "...",
  "full_script": "hook_line + body + cta as one continuous script",
  "word_count": <integer>,
  "tone": "authentic|educational|storytelling",
  "notes": "what you changed and why"
}"""


def check_authenticity(
    script: dict,
    topic: str = "",
) -> dict:
    """
    Run the Human Taste Test + Trust & Authenticity check on a script dict.
    Returns the check result with scores and verdict.
    """
    full_script = script.get("full_script", "")
    hook = script.get("hook_line", "")
    cta = script.get("cta", "")

    user_prompt = f"""Evaluate this TikTok script:

Topic: {topic}
---
HOOK: {hook}

BODY + CTA:
{script.get("body", "")}
{cta}
---
Full script ({script.get("word_count", "?")} words):
{full_script}

Score it. Be brutally honest — you would never post cringe content."""

    log.info("Running authenticity check...")
    result = call_json(
        system=_TASTE_SYSTEM,
        user=user_prompt,
        model=SONNET,
        max_tokens=600,
        temperature=0.3,  # Low temp — we want consistent scoring
    )

    overall = result.get("overall_score")
    if overall is None:
        scores = result.get("scores", {})
        if scores:
            overall = round(sum(scores.values()) / len(scores), 1)
            result["overall_score"] = overall

    result["passed"] = overall >= 7.0 if overall is not None else False
    result["verdict"] = "APPROVED" if result["passed"] else "REVISION_NEEDED"

    log.info(
        "Authenticity check: score=%.1f verdict=%s flags=%s",
        overall or 0,
        result["verdict"],
        result.get("red_flags", []),
    )
    return result


def revise_script(
    original_script: dict,
    check_result: dict,
    topic: str = "",
) -> dict:
    """Rewrite the script to fix the issues found by the authenticity check."""
    user_prompt = f"""Revise this TikTok script to fix these problems:

Original script:
HOOK: {original_script.get("hook_line", "")}
BODY: {original_script.get("body", "")}
CTA: {original_script.get("cta", "")}
Word count: {original_script.get("word_count", "?")}

Topic: {topic}

Problems found (score was {check_result.get("overall_score", "?")}):
Red flags: {check_result.get("red_flags", [])}
Revision notes: {check_result.get("revision_notes", "")}

Things that worked (keep these):
Green flags: {check_result.get("green_flags", [])}

Rewrite it to score 7+ on all dimensions. Return as JSON."""

    log.info("Revising script to fix: %s", check_result.get("red_flags", []))
    revised = call_json(
        system=_REVISION_SYSTEM,
        user=user_prompt,
        model=SONNET,
        max_tokens=600,
        temperature=0.85,
    )

    # Recompute word count
    full = revised.get("full_script", "")
    if full:
        revised["word_count"] = len(full.split())

    return revised


def run_authenticity_loop(
    script: dict,
    topic: str = "",
    max_revisions: int = 2,
) -> tuple[dict, dict, int]:
    """
    Run the authenticity check with up to max_revisions revision loops.

    Returns:
        (final_script, final_check_result, revision_count)

    Raises:
        ValueError if script still fails after max_revisions
    """
    current_script = script
    revision_count = 0

    for attempt in range(max_revisions + 1):
        check = check_authenticity(current_script, topic=topic)

        if check["passed"]:
            log.info(
                "Script passed authenticity check on attempt %d (score=%.1f)",
                attempt + 1,
                check.get("overall_score", 0),
            )
            current_script["authenticity_score"] = check.get("overall_score")
            return current_script, check, revision_count

        if attempt < max_revisions:
            log.info(
                "Attempt %d failed (score=%.1f) — revising script...",
                attempt + 1,
                check.get("overall_score", 0),
            )
            current_script = revise_script(current_script, check, topic=topic)
            revision_count += 1
        else:
            log.warning(
                "Script failed after %d revision(s) — final score=%.1f. "
                "Returning best version anyway.",
                revision_count,
                check.get("overall_score", 0),
            )
            # Return with low score rather than crashing — let human review decide
            current_script["authenticity_score"] = check.get("overall_score")
            current_script["authenticity_failed"] = True
            return current_script, check, revision_count

    # Should never reach here
    return current_script, {}, revision_count
