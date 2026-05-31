"""
Caption & Hashtag Agent.

Generates:
- Caption text (≤ 150 chars) that reads like a personal thought, not an ad
- Hashtag mix (12-18 tags):
    40% niche/low-competition (< 500M views)
    40% mid-tier (500M–5B views)
    20% trend/category-specific

FTC note: If a product with affiliate link is included, #ad is automatically injected.
"""
from typing import Optional

from tools.claude_client import HAIKU, call_json
from tools.utils import log

# Hashtag banks by content category (supplemented by Claude's output)
_NICHE_HASHTAGS: dict[str, list[str]] = {
    "beauty": ["#skincaretips", "#drugstorebeauty", "#skincareobsessed", "#beautyfinds", "#glowyskin"],
    "skincare": ["#skincaretips", "#acneskin", "#dryskin", "#skincareroutine", "#drugstoreskincare"],
    "lifestyle": ["#lifestylecheck", "#dailylifestyle", "#aestheticlife", "#lifehack", "#productfinds"],
    "wellness": ["#wellnesstips", "#selfcaretips", "#morningroutine", "#healthylifestyle", "#mindfuliving"],
    "organization": ["#organizedlife", "#cleaningtips", "#roomdecor", "#organizationhacks", "#tidyup"],
    "budget": ["#budgetfinds", "#amazonfind", "#thriftedfinds", "#savemoney", "#affordableproducts"],
    "dorm": ["#dormlife", "#dormroom", "#collegelife", "#dormessentials", "#dormtok"],
    "gadgets": ["#coolgadgets", "#productreview", "#musthaveproducts", "#techfinds", "#usefulproducts"],
    "bridge": ["#lifehack", "#productfinds", "#dailyroutine", "#mustknow", "#recommendthis"],
    "fashion": ["#fashionfinds", "#outfitcheck", "#ootd", "#styletips", "#affordablefashion"],
}

_MID_HASHTAGS: dict[str, list[str]] = {
    "beauty": ["#beauty", "#makeup", "#skincare", "#glowup", "#beautyadvice"],
    "skincare": ["#skincare", "#skintok", "#skincareroutine", "#clearskin", "#glowskin"],
    "lifestyle": ["#lifestyle", "#productivity", "#dailyroutine", "#livingmybestlife", "#vlog"],
    "wellness": ["#wellness", "#selfcare", "#healthtips", "#morningroutine", "#wellbeing"],
    "organization": ["#organization", "#cleaning", "#homeideas", "#declutter", "#aesthetic"],
    "budget": ["#savingmoney", "#budgetfriendly", "#dealsandsteals", "#shopsmarter", "#affordablelife"],
    "dorm": ["#college", "#dormroom", "#collegelife", "#students", "#dormdecor"],
    "gadgets": ["#gadgets", "#amazonfinds", "#productreview", "#techgadgets", "#musthave"],
    "bridge": ["#lifestyle", "#productreview", "#dailylife", "#recommendation", "#trending"],
    "fashion": ["#fashion", "#style", "#ootd", "#outfitoftheday", "#fashiontok"],
}

_UNIVERSAL_TIKTOK = ["#tiktokshop", "#tiktokmademebuyit", "#fyp", "#foryou", "#foryoupage"]

_CAPTION_SYSTEM = """You are writing a TikTok caption for a lifestyle/beauty account.

The caption should:
- Sound like a personal thought or off-the-cuff comment, NOT a description of the video
- Be 1-2 short sentences maximum (under 150 characters)
- Feel conversational and a tiny bit cryptic (make people want to watch to get context)
- NOT start with "Check out" or "Watch this" or "In this video"
- Optionally end with a soft question to drive comments

Examples of great captions:
  "finally found one that actually works 🤍"
  "the before and after has me in shock"
  "my skin has never looked like this before"
  "okay this changed everything"
  "i wasn't expecting to be obsessed with this"

Return a JSON object with:
{
  "caption": "the caption text (under 150 chars)",
  "caption_tone": "one word describing the tone",
  "engagement_hook": "optional soft question to drive comments (or null)"
}"""


def generate_caption(
    topic: str,
    script: dict,
    content_category: str = "bridge",
    product_name: Optional[str] = None,
    has_affiliate: bool = False,
) -> dict:
    """Generate caption text (without hashtags)."""
    user_prompt = f"""Write a TikTok caption for this video:

Topic: {topic}
Content category: {content_category}
Hook line: {script.get("hook_line", "")}
{"Product featured: " + product_name if product_name else "No specific product"}
{"Has affiliate link: YES (needs #ad)" if has_affiliate else ""}

Write a short, scroll-stopping caption. Under 150 characters. Return as JSON."""

    return call_json(
        system=_CAPTION_SYSTEM,
        user=user_prompt,
        model=HAIKU,  # Simple task — use cheaper model
        max_tokens=200,
        temperature=0.8,
    )


def build_hashtag_set(
    content_category: str = "bridge",
    has_affiliate: bool = False,
    trending_hashtags: Optional[list[str]] = None,
    count: int = 15,
) -> list[str]:
    """
    Build a hashtag mix:
    40% niche + 40% mid-tier + 20% universal/trending
    Plus #ad if affiliate link present.
    """
    cat = content_category if content_category in _NICHE_HASHTAGS else "bridge"

    niche = _NICHE_HASHTAGS.get(cat, _NICHE_HASHTAGS["bridge"])
    mid = _MID_HASHTAGS.get(cat, _MID_HASHTAGS["bridge"])
    universal = _UNIVERSAL_TIKTOK.copy()

    # Add trending hashtags from DB/trend agent (Phase 3+)
    if trending_hashtags:
        universal = trending_hashtags[:3] + universal

    target_niche = max(1, int(count * 0.4))
    target_mid = max(1, int(count * 0.4))
    target_universal = count - target_niche - target_mid

    selected = (
        niche[:target_niche]
        + mid[:target_mid]
        + universal[:target_universal]
    )

    # FTC compliance — inject #ad if affiliate link
    if has_affiliate and "#ad" not in selected:
        selected = ["#ad"] + selected

    # Deduplicate preserving order
    seen: set[str] = set()
    result = []
    for tag in selected:
        normalized = tag.lower() if tag.startswith("#") else f"#{tag.lower()}"
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized if tag.startswith("#") else f"#{tag}")

    log.info("Generated %d hashtags for category=%s affiliate=%s", len(result), cat, has_affiliate)
    return result


def generate_full_caption(
    topic: str,
    script: dict,
    content_category: str = "bridge",
    product_name: Optional[str] = None,
    has_affiliate: bool = False,
    trending_hashtags: Optional[list[str]] = None,
) -> dict:
    """
    Full caption generation: text + hashtags combined.

    Returns:
    {
      "caption": "...",
      "hashtags": ["#tag1", "#tag2", ...],
      "full_caption_with_tags": "caption text\n\n#tag1 #tag2 ...",
      "has_ad_disclosure": bool
    }
    """
    log.info("Generating caption for: %r", topic)

    caption_data = generate_caption(topic, script, content_category, product_name, has_affiliate)
    hashtags = build_hashtag_set(content_category, has_affiliate, trending_hashtags)

    caption_text = caption_data.get("caption", "")
    engagement_hook = caption_data.get("engagement_hook")
    if engagement_hook:
        caption_text = f"{caption_text} {engagement_hook}".strip()

    hashtag_string = " ".join(hashtags)
    full = f"{caption_text}\n\n{hashtag_string}"

    return {
        "caption": caption_text,
        "hashtags": hashtags,
        "full_caption_with_tags": full,
        "has_ad_disclosure": "#ad" in hashtags,
        "hashtag_count": len(hashtags),
    }
