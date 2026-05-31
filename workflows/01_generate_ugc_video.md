# Workflow 01: Generate UGC Video (Phase 1 — Manual Pipeline)

## Objective
Generate one locally-stored UGC-style TikTok video. No posting. This is the Phase 1 manual flow — you review every video before anything happens.

## Prerequisites

### One-time setup
1. Copy `.env.example` to `.env`
2. Add your `ANTHROPIC_API_KEY` to `.env`
3. Add your `PEXELS_API_KEY` to `.env` (get from pexels.com/api)
4. Start MoneyPrinterTurbo:
   ```powershell
   cd "c:\Users\Owner\OneDrive\Desktop\SKook\TIKTOK UGC _ MONEY PRINTER LLM\MoneyPrinterTurbo"
   python main.py
   ```
   Wait until you see: `Uvicorn running on http://0.0.0.0:8080`

### Per-run inputs you'll provide
- **Topic**: What the video is about (be specific)
- **Product** (optional): Product name to feature
- **Category** (optional): content category — if unsure, omit and let Creative Director choose
- **Phase**: Current audience transition phase (1-4) — check `.env` TRANSITION_PHASE

---

## Running the Pipeline

### Quickstart
```powershell
cd "c:\Users\Owner\OneDrive\Desktop\SKook\TIKTOK UGC _ MONEY PRINTER LLM"
python tools/generate_video.py --topic "YOUR TOPIC HERE"
```

### Script-only (no video, fast, cheap)
```powershell
python tools/generate_video.py --topic "..." --dry-run
```
Use `--dry-run` to test topics, iterate on scripts, and validate quality before spending time on video generation.

### With a product
```powershell
python tools/generate_video.py \
  --topic "CeraVe Moisturizer review" \
  --product "CeraVe Moisturizing Cream" \
  --product-details "Fragrance-free, ceramides, $14 at Target" \
  --affiliate \
  --category skincare
```
`--affiliate` automatically adds `#ad` to the hashtags (FTC compliance).

### Specifying audience transition phase
```powershell
python tools/generate_video.py --topic "..." --phase 2
```
Defaults to `TRANSITION_PHASE` in `.env` if not specified.

---

## What the Pipeline Does

```
Step 1: Creative Director Brief
  → Claude Sonnet chooses angle, format, emotional trigger, tone

Step 2: Script Agent
  → Writes full hook + body + CTA (≤ 80 words, first-person, casual)

Step 3: Hook Optimization
  → Generates 3 hook variants, scores each on curiosity/authenticity/retention
  → Picks best hook automatically

Step 4: Human Taste Test (Trust & Authenticity Agent)
  → Scores script 1-10 on: authenticity, naturalness, trust, tiktok_native, non_salesy
  → If score < 7: auto-revises (up to 2 attempts)
  → If still < 7 after revisions: flags for your manual review

Step 5: Caption + Hashtag Generator
  → Caption: ≤ 150 chars, personal/cryptic, NOT ad-like
  → Hashtags: 15 tags — 40% niche + 40% mid-tier + 20% universal
  → If affiliate: adds #ad automatically

Step 6: Video Generation (MoneyPrinterTurbo)
  → Submits script to MPT API
  → Polls until complete (2-5 minutes)
  → Downloads MP4 to .tmp/videos/

Step 7: Save to SQLite DB
  → Records all metadata in .tmp/database.db
  → Saves full output JSON to .tmp/scripts/
```

---

## Understanding the Output

### Terminal output sections
1. **Script** — full hook + body + CTA
2. **Alternative hooks** — the 2 hooks that weren't selected (sometimes useful)
3. **Authenticity score** — should be 7+. If it shows REVISION_NEEDED, review carefully
4. **Caption** — ready to paste into TikTok
5. **Hashtags** — copy-paste ready
6. **Video path** — where your MP4 is saved

### Files created per run
- `.tmp/videos/{task_id}.mp4` — the generated video
- `.tmp/scripts/{run_id}.json` — full metadata (script, caption, hooks, scores, paths)
- `.tmp/database.db` — SQLite database with all runs

---

## Human Review Checklist (Do This Before Posting Anything)

After the pipeline completes, watch the video and check:

**Script / Audio:**
- [ ] Does it sound like a real person, not an AI?
- [ ] Is the pacing natural? (not too fast, not robotic)
- [ ] Does the hook make you want to keep watching?
- [ ] Is the CTA reluctant/natural? ("link's in bio" not "buy now!")
- [ ] If affiliate product: does it sound like a genuine recommendation?

**Visual:**
- [ ] Are the b-roll clips relevant to the topic?
- [ ] Are subtitles readable and accurate?
- [ ] Is the music level low enough not to overpower the voice?
- [ ] Is it 9:16 portrait format?

**Compliance:**
- [ ] If featuring an affiliate product: is #ad in the hashtags? ✓ (auto-added)
- [ ] No false medical/health claims ("cures", "guarantees", "clinically proven")
- [ ] No copyrighted music (MPT uses royalty-free BGM by default)

**Audience fit:**
- [ ] Is this appropriate for current transition phase ({current_phase})?
- [ ] Would a real 25-year-old lifestyle creator post this?
- [ ] Does it feel authentic or like AI-generated dropshipping content?

**Decision:**
- APPROVED → Save video, schedule for posting when Phase 5 is ready
- NEEDS EDITS → Note what to fix, re-run with adjusted topic/params
- REJECTED → Do NOT post. Note why in your review log.

---

## Tips for Better Results

### Improving script quality
- Be SPECIFIC in your topic: "3 drugstore moisturizers under $15 for dry skin" > "moisturizer recommendations"
- Add audience context: who are they, what problem do they have?
- Reference a real trend or moment: "everyone's been asking about..." 
- For Phase 1 (bridge content), avoid beauty-specific topics — use lifestyle/gadgets

### If the script sounds robotic
- Re-run with `--dry-run` and tweak the topic to be more personal/specific
- Try different content categories with `--category`
- Check if word count is over 80 — shorter = more natural

### If the video b-roll doesn't match
- The b-roll terms are auto-selected by content category
- If wrong: manually edit `tools/mpt_client.py` BROLL_TERMS to add better search terms

### Voice options
- `en-US-JennyNeural` (default) — young, conversational, lifestyle feel
- `en-US-AriaNeural` — warmer, slightly more mature
- `en-US-MichelleNeural` — friendly, relatable
- Try: `python tools/generate_video.py --topic "..." --voice en-US-AriaNeural`

---

## Troubleshooting

### "MoneyPrinterTurbo is not running"
Start it: `cd MoneyPrinterTurbo && python main.py`
Wait for the Uvicorn startup message before running the pipeline.

### "Missing required environment variable: ANTHROPIC_API_KEY"
Add your key to `.env`. Get it at console.anthropic.com.

### "Failed to parse Claude JSON response"
Rare — Claude occasionally produces malformed JSON. Just re-run.

### Video generation hangs > 5 minutes
MPT may be stuck waiting for Pexels API. Check that `PEXELS_API_KEY` is set in `config.toml` inside the MoneyPrinterTurbo directory (not just .env).

### Authenticity score keeps failing
The script topic may be too product-forward. Try a softer angle:
- Instead of: "CeraVe review" → try: "my dry skin finally cleared up" (mention product naturally mid-script)

---

## Batch Mode (run multiple topics quickly)

For testing multiple topics at once without video generation:
```powershell
$topics = @(
    "My skincare routine changed after I found this",
    "3 things I keep repurchasing every month",
    "The $12 find everyone needs in their bathroom"
)
foreach ($t in $topics) {
    python tools/generate_video.py --topic $t --dry-run
    Start-Sleep 2
}
```

---

## Logging & Record Keeping

Every run is saved to:
- `.tmp/database.db` → query with any SQLite viewer
- `.tmp/scripts/{run_id}.json` → full output per run

Useful queries:
```sql
-- See all videos with their authenticity scores
SELECT id, status, content_category, authenticity_score, created_at FROM videos ORDER BY created_at DESC;

-- See all scripts with word count and approval status
SELECT subject, word_count, authenticity_score, approved FROM scripts ORDER BY created_at DESC;

-- See all hooks with their scores
SELECT hook_text, hook_type, emotion FROM hooks ORDER BY created_at DESC;
```
