"""
Script generator — two-stage: Creative Director brief → Script Agent output.

Stage 1 (Creative Director):  Chooses angle, format, hook strategy, tone.
Stage 2 (Script Agent):       Writes the full hook + body + CTA (≤ 80 words).
"""
import json
from typing import Optional

from tools.claude_client import SONNET, call_json
from tools.utils import log, new_id, save_script

# ── System prompts ────────────────────────────────────────────────────────────

_CREATIVE_DIRECTOR_SYSTEM = """You are a Creative Director for a TikTok lifestyle and beauty account.
Your job is to design the creative brief for a short UGC-style video.

The account is transitioning from a male audience to a female audience aged 22-34 interested in
beauty, skincare, wellness, lifestyle, and affordable finds.

Content should feel:
- Authentic, like a real creator's genuine recommendation
- NOT like an ad or sponsored content
- Native to TikTok (casual, fast, entertaining)
- Trust-based: "I found this and it actually works"

Formats that work well:
- "I tried this so you don't have to"
- "Things I actually use every day"
- "This changed my routine"
- "Found this and can't stop recommending it"
- "Worth the hype?"
- "Hidden gem vs. overhyped product"
- Problem → Solution storytelling
- Before/after with authentic framing

Return a JSON creative brief with these fields:
{
  "angle": "the specific creative angle/hook strategy",
  "format": "the content format name",
  "emotional_trigger": "curiosity|fomo|aspiration|relatability|problem_solving",
  "tone": "authentic|educational|storytelling|listicle",
  "product_integration": "how to integrate the product naturally (if any)",
  "cta_style": "reluctant|soft|story_close",
  "content_category": "bridge|lifestyle|beauty|skincare|wellness|organization|budget|dorm|gadgets",
  "b_roll_style": "one sentence describing the visual feel of the b-roll"
}"""

_SCRIPT_AGENT_SYSTEM = """You are a TikTok UGC script writer. You write short, authentic scripts
for a female lifestyle/beauty creator aged 26. Your scripts sound like a real person talking
to camera, NOT like marketing copy.

MANDATORY RULES:
1. Maximum 80 words for the ENTIRE script (30-40 seconds at natural speaking pace)
2. First person, present tense: "I literally use this every morning" — never "users report..."
3. Include ONE natural imperfection: a false start, self-correction, or casual aside
   Example: "Okay so — wait, I need to show you the before first"
4. Use natural fillers: "honestly," "literally," "like," "okay so," "real talk," "lowkey"
5. Start MID-THOUGHT, never with a scripted question like "Have you ever wondered..."
   Bad: "Have you ever struggled with dry skin?"
   Good: "I've been dealing with dry skin for years and I finally—"
6. ONE specific personal detail that grounds the story
   Example: "I found this when I was shopping for my college dorm room"
7. CTA must sound RELUCTANT, not pushy:
   Good: "link's in bio if you want it"
   Bad: "Click the link now to get yours!"
8. No bullet-point phrasing in speech. Humans ramble naturally.
9. If featuring a product, name it casually: "this little serum" not "THE PRODUCT NAME"
10. No hashtags or emojis in the script — those go in the caption

Return valid JSON with exactly these fields:
{
  "hook_line": "the very first sentence (3 seconds max — most critical part)",
  "body": "the rest of the script after the hook",
  "cta": "the closing call to action line",
  "full_script": "hook_line + body + cta combined as one continuous script",
  "word_count": <integer>,
  "tone": "authentic|educational|storytelling",
  "notes": "any notes about how this should be delivered/performed"
}"""


def generate_creative_brief(
    topic: str,
    audience: str = "women 22-34 interested in beauty and lifestyle",
    product_name: Optional[str] = None,
    content_category: Optional[str] = None,
    transition_phase: int = 1,
) -> dict:
    """Stage 1: Creative Director generates the brief."""
    product_context = f"Product to feature: {product_name}" if product_name else "No specific product — general lifestyle/discovery content"
    phase_context = {
        1: "Transition Phase 1: Use bridge content that appeals to both male and female audiences. Focus on universal lifestyle, gadgets, or subtle wellness content. Avoid overtly female-targeted content.",
        2: "Transition Phase 2: Lean toward female lifestyle content — morning routines, organization, wellness. Soft product introductions are OK. Still avoid hardcore beauty content.",
        3: "Transition Phase 3: Full female lifestyle content. Beauty, skincare, and product reviews welcome. Can now feature affiliate products with #ad.",
        4: "Transition Phase 4: Full monetization. Beauty, skincare, lifestyle products. Optimize for TikTok Shop clicks.",
    }.get(transition_phase, "")

    user_prompt = f"""Create a creative brief for this TikTok video:

Topic: {topic}
Target audience: {audience}
{product_context}
{"Content category preference: " + content_category if content_category else ""}

{phase_context}

Return the creative brief as JSON."""

    log.info("Generating creative brief for: %r", topic)
    brief = call_json(
        system=_CREATIVE_DIRECTOR_SYSTEM,
        user=user_prompt,
        model=SONNET,
        max_tokens=512,
        temperature=0.8,
    )
    log.info("Creative brief: format=%r angle=%r", brief.get("format"), brief.get("angle"))
    return brief


def generate_script(
    topic: str,
    brief: dict,
    audience: str = "women 22-34 interested in beauty and lifestyle",
    product_name: Optional[str] = None,
    product_details: Optional[str] = None,
) -> dict:
    """Stage 2: Script Agent writes the full script."""
    product_block = ""
    if product_name:
        product_block = f"""
Product to feature (naturally, not salesy):
  Name: {product_name}
  Details: {product_details or "no additional details"}
  Integration style: {brief.get("product_integration", "mention casually at the end")}
"""

    user_prompt = f"""Write a TikTok UGC script for this video:

Topic: {topic}
Target audience: {audience}
{product_block}
Creative brief:
  Angle: {brief.get("angle")}
  Format: {brief.get("format")}
  Emotional trigger: {brief.get("emotional_trigger")}
  Tone: {brief.get("tone")}
  CTA style: {brief.get("cta_style")}

Remember: Maximum 80 words total. Sound like a real 26-year-old creator, not marketing copy.
Return as JSON."""

    log.info("Generating script...")
    script = call_json(
        system=_SCRIPT_AGENT_SYSTEM,
        user=user_prompt,
        model=SONNET,
        max_tokens=600,
        temperature=0.85,
    )

    # Enforce word count check
    full = script.get("full_script", "")
    actual_wc = len(full.split())
    script["word_count"] = actual_wc
    if actual_wc > 90:
        log.warning("Script is %d words (target ≤ 80) — may need trimming", actual_wc)

    log.info("Script generated: %d words, hook=%r", actual_wc, script.get("hook_line", "")[:60])
    return script


def generate_full_script(
    topic: str,
    audience: str = "women 22-34 interested in beauty and lifestyle",
    product_name: Optional[str] = None,
    product_details: Optional[str] = None,
    content_category: Optional[str] = None,
    transition_phase: int = 1,
    save: bool = True,
) -> dict:
    """
    Full two-stage pipeline: brief → script.
    Returns combined result dict. Optionally saves to SQLite.
    """
    brief = generate_creative_brief(
        topic=topic,
        audience=audience,
        product_name=product_name,
        content_category=content_category,
        transition_phase=transition_phase,
    )

    script = generate_script(
        topic=topic,
        brief=brief,
        audience=audience,
        product_name=product_name,
        product_details=product_details,
    )

    result = {
        "id": new_id(),
        "subject": topic,
        "hook_line": script.get("hook_line", ""),
        "body": script.get("body", ""),
        "cta": script.get("cta", ""),
        "full_script": script.get("full_script", ""),
        "word_count": script.get("word_count", 0),
        "tone": script.get("tone", brief.get("tone", "authentic")),
        "content_category": brief.get("content_category", content_category or "bridge"),
        "brief": brief,
        "notes": script.get("notes", ""),
        "generation_prompt": f"topic={topic} audience={audience}",
    }

    if save:
        save_script(result)

    return result
