"""
Phase 1 CLI — Full UGC Video Pipeline Orchestrator.

Usage:
  python tools/generate_video.py --topic "Top 3 drugstore skincare finds under $15"
  python tools/generate_video.py --topic "..." --product "CeraVe Moisturizer" --affiliate
  python tools/generate_video.py --topic "..." --category beauty --phase 2
  python tools/generate_video.py --topic "..." --dry-run   # script only, no video

Full pipeline:
  1. Creative Director Brief
  2. Script Agent (hook + body + CTA)
  3. Hook Optimization (3 variants → best)
  4. Trust & Authenticity Check (Human Taste Test, up to 2 revisions)
  5. Caption + Hashtag Generator
  6. Video Generation (MoneyPrinterTurbo)
  7. Save to SQLite DB
  8. Print results to terminal
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

# UTF-8 output on Windows so logging doesn't crash on special chars
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from tools.authenticity_checker import run_authenticity_loop
from tools.caption_generator import generate_full_caption
from tools.hook_generator import optimize_hooks
from tools.mpt_client import generate_video, is_mpt_running
from tools.script_generator import generate_full_script
from tools.utils import (
    current_transition_phase,
    init_db,
    log,
    new_id,
    save_script_file,
    save_video,
    scripts_dir,
    update_video_status,
    use_sqlite,
)

# ── ANSI colors for terminal output ──────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_section(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{'-'*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'-'*60}{RESET}")


def print_result(label: str, value: str, good: bool = True) -> None:
    color = GREEN if good else RED
    print(f"  {color}{BOLD}{label}:{RESET} {value}")


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(
    topic: str,
    audience: str = "women 22-34 interested in beauty and lifestyle",
    product_name: str | None = None,
    product_details: str | None = None,
    has_affiliate: bool = False,
    content_category: str | None = None,
    transition_phase: int | None = None,
    dry_run: bool = False,
    voice: str = "en-US-JennyNeural",
) -> dict:
    """
    Run the full Phase 1 pipeline. Returns a results dict.
    dry_run=True skips video generation (script + caption only).
    """
    run_id = new_id()
    phase = transition_phase or current_transition_phase()
    started = time.time()

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  TikTok UGC Pipeline — Run {run_id[:8]}{RESET}")
    print(f"{BOLD}  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"  Topic:    {topic}")
    print(f"  Audience: {audience}")
    print(f"  Phase:    {phase}")
    if product_name:
        print(f"  Product:  {product_name} {'(affiliate)' if has_affiliate else ''}")
    if dry_run:
        print(f"  {YELLOW}DRY RUN — skipping video generation{RESET}")

    # ── Stage 1-2: Script (Creative Director + Script Agent) ──────────────
    print_section("Stage 1-2: Script Generation")
    script_result = generate_full_script(
        topic=topic,
        audience=audience,
        product_name=product_name,
        product_details=product_details,
        content_category=content_category,
        transition_phase=phase,
        save=False,  # Save after authenticity check passes
    )

    cat = script_result.get("content_category", "bridge")
    print_result("Content category", cat)
    print_result("Format", script_result.get("brief", {}).get("format", "unknown"))
    print_result("Angle", script_result.get("brief", {}).get("angle", "unknown"))
    print(f"\n  {BOLD}Draft script ({script_result.get('word_count', '?')} words):{RESET}")
    print(f"  {script_result.get('full_script', '')}")

    # ── Stage 3: Hook Optimization ────────────────────────────────────────
    print_section("Stage 3: Hook Optimization")
    best_hook, all_hooks = optimize_hooks(
        topic=topic,
        script_body=script_result.get("body", ""),
        content_category=cat,
        brief_angle=script_result.get("brief", {}).get("angle", ""),
    )

    print_result("Best hook", best_hook.get("hook_text", ""), good=True)
    print_result("Hook type", best_hook.get("hook_type", ""), good=True)
    print_result("Hook score", str(best_hook.get("total_score", 0)), good=best_hook.get("total_score", 0) >= 28)
    print(f"\n  {YELLOW}Alternative hooks:{RESET}")
    for i, h in enumerate(all_hooks[1:], 2):
        print(f"  {i}. [{h.get('total_score', 0)}/40] {h.get('hook_text', '')}")

    # Update script with winning hook
    script_result["hook_line"] = best_hook.get("hook_text", script_result.get("hook_line", ""))
    script_result["hook_id"] = best_hook.get("id")
    # Rebuild full_script with winning hook
    script_result["full_script"] = (
        f"{script_result['hook_line']} {script_result.get('body', '')} {script_result.get('cta', '')}"
    ).strip()

    # ── Stage 4: Authenticity Check ───────────────────────────────────────
    print_section("Stage 4: Trust & Authenticity Check")
    final_script, check_result, revisions = run_authenticity_loop(
        script=script_result,
        topic=topic,
        max_revisions=2,
    )

    score = check_result.get("overall_score", 0)
    passed = check_result.get("passed", False)
    color = GREEN if passed else RED

    print(f"  {color}{BOLD}Score: {score}/10 — {check_result.get('verdict', 'UNKNOWN')}{RESET}")
    print(f"  Revisions applied: {revisions}")
    if check_result.get("green_flags"):
        print(f"  {GREEN}✓ {', '.join(check_result['green_flags'][:3])}{RESET}")
    if check_result.get("red_flags"):
        print(f"  {RED}✗ {', '.join(check_result['red_flags'][:3])}{RESET}")

    if not passed:
        print(f"\n  {YELLOW}⚠  Script scored below 7/10 after {revisions} revision(s).{RESET}")
        print(f"  {YELLOW}   Proceeding but flagging for manual review.{RESET}")

    print(f"\n  {BOLD}Final script ({final_script.get('word_count', '?')} words):{RESET}")
    print(f"  {final_script.get('full_script', '')}")

    # Save script to DB now that it's been checked
    final_script["authenticity_score"] = score
    final_script["approved"] = passed
    script_id = final_script.get("id") or new_id()
    final_script["id"] = script_id

    from tools.utils import save_script
    save_script(final_script)

    # ── Stage 5: Caption + Hashtags ───────────────────────────────────────
    print_section("Stage 5: Caption & Hashtags")
    caption_result = generate_full_caption(
        topic=topic,
        script=final_script,
        content_category=cat,
        product_name=product_name,
        has_affiliate=has_affiliate,
    )

    print_result("Caption", caption_result.get("caption", ""))
    if caption_result.get("has_ad_disclosure"):
        print(f"  {GREEN}✓ #ad disclosure included (FTC compliance){RESET}")
    print(f"  Hashtags ({caption_result.get('hashtag_count', 0)}):")
    print(f"  {' '.join(caption_result.get('hashtags', []))}")

    # ── Stage 6: Video Generation ─────────────────────────────────────────
    video_path = None
    mpt_task_id = None

    if not dry_run:
        print_section("Stage 6: Video Generation (MoneyPrinterTurbo)")

        if not is_mpt_running():
            print(f"  {RED}✗ MoneyPrinterTurbo is not running!{RESET}")
            print(f"  Start it: cd MoneyPrinterTurbo && python main.py")
            print(f"  {YELLOW}Skipping video generation — all other output saved.{RESET}")
        else:
            print(f"  Submitting to MPT... (this takes 2-5 minutes)")
            try:
                mpt_task_id, video_path = generate_video(
                    script=final_script.get("full_script", ""),
                    subject=topic,
                    content_category=cat,
                    voice_name=voice,
                )
                print_result("Video saved", str(video_path), good=True)
                print(f"  Size: {video_path.stat().st_size / 1_048_576:.1f} MB")
            except Exception as e:
                print(f"  {RED}✗ Video generation failed: {e}{RESET}")
                log.error("Video generation failed: %s", e)
    else:
        print_section("Stage 6: Video Generation (SKIPPED — dry run)")

    # ── Stage 7: Save to DB ───────────────────────────────────────────────
    print_section("Stage 7: Saving to Database")
    video_id = new_id()
    video_status = "pending_review" if video_path else "draft"

    video_data = {
        "id": video_id,
        "status": video_status,
        "content_category": cat,
        "transition_phase": phase,
        "script_id": script_id,
        "hook_id": best_hook.get("id"),
        "caption": caption_result.get("caption", ""),
        "hashtags": caption_result.get("hashtags", []),
        "mpt_task_id": mpt_task_id,
        "final_video_path": str(video_path) if video_path else None,
        "authenticity_score": score,
        "voice_name": voice,
        "video_params": {"content_category": cat, "voice": voice},
    }
    save_video(video_data)
    print_result("Video record saved", f"ID={video_id[:8]}", good=True)
    print_result("Status", video_status)

    # Save full output JSON to scripts dir
    output = {
        "run_id": run_id,
        "video_id": video_id,
        "topic": topic,
        "content_category": cat,
        "transition_phase": phase,
        "script": {
            "id": script_id,
            "full_script": final_script.get("full_script"),
            "hook": best_hook.get("hook_text"),
            "word_count": final_script.get("word_count"),
            "authenticity_score": score,
            "authenticity_passed": passed,
        },
        "caption": caption_result.get("caption"),
        "hashtags": caption_result.get("hashtags"),
        "full_caption_with_tags": caption_result.get("full_caption_with_tags"),
        "video_path": str(video_path) if video_path else None,
        "mpt_task_id": mpt_task_id,
        "duration_sec": round(time.time() - started, 1),
        "all_hooks": [h.get("hook_text") for h in all_hooks],
    }

    output_file = save_script_file(run_id, output)

    # ── Final Summary ─────────────────────────────────────────────────────
    elapsed = round(time.time() - started, 1)
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}{GREEN}  PIPELINE COMPLETE in {elapsed}s{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"\n  {BOLD}FINAL SCRIPT:{RESET}")
    print(f"  {final_script.get('full_script', '')}")
    print(f"\n  {BOLD}CAPTION + TAGS:{RESET}")
    print(f"  {caption_result.get('full_caption_with_tags', '')}")
    if video_path:
        print(f"\n  {BOLD}VIDEO:{RESET} {video_path}")
    print(f"\n  {BOLD}Output saved:{RESET} {output_file}")
    print(f"  {BOLD}Video ID:{RESET} {video_id}")
    print()

    return output


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="TikTok UGC Video Pipeline — Phase 1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/generate_video.py --topic "Top 3 drugstore skincare finds under $15"
  python tools/generate_video.py --topic "Morning routine essentials" --category lifestyle
  python tools/generate_video.py --topic "CeraVe review" --product "CeraVe Moisturizer" --affiliate
  python tools/generate_video.py --topic "..." --dry-run  # Script + caption only, no video
        """,
    )
    parser.add_argument("--topic", required=True, help="Video topic / subject")
    parser.add_argument("--audience", default="women 22-34 interested in beauty and lifestyle")
    parser.add_argument("--product", dest="product_name", default=None, help="Product name to feature")
    parser.add_argument("--product-details", default=None, help="Product description/details")
    parser.add_argument("--affiliate", action="store_true", help="Has affiliate link (adds #ad)")
    parser.add_argument("--category", dest="content_category", default=None,
                        choices=["bridge", "lifestyle", "beauty", "skincare", "wellness",
                                 "organization", "budget", "dorm", "gadgets", "fashion"],
                        help="Content category (default: auto-selected)")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4],
                        default=None, help="Audience transition phase (default: from .env)")
    parser.add_argument("--voice", default="en-US-JennyNeural",
                        help="TTS voice name (default: en-US-JennyNeural)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate script + caption only, skip video generation")
    args = parser.parse_args()

    # Init DB on first run
    if use_sqlite():
        init_db()

    run_pipeline(
        topic=args.topic,
        audience=args.audience,
        product_name=args.product_name,
        product_details=args.product_details,
        has_affiliate=args.affiliate,
        content_category=args.content_category,
        transition_phase=args.phase,
        dry_run=args.dry_run,
        voice=args.voice,
    )


if __name__ == "__main__":
    main()
