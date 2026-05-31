"""
MoneyPrinterTurbo API client.

API reference (from schema.py + video.py controller):
  POST /v1/video/videos  → { data: { task_id } }
  GET  /v1/video/tasks/{task_id} → { data: { state, progress, videos, combined_videos } }

Task states: 0=queued, 1=processing, 2=complete, 3=failed, 4=stopped
"""
import shutil
import time
from pathlib import Path
from typing import Optional

import requests

from tools.utils import (
    get_env,
    log,
    retry,
    videos_dir,
)

_BASE_URL = get_env("MPT_BASE_URL", "http://127.0.0.1:8080")
_TIMEOUT = int(get_env("MPT_API_TIMEOUT", "300"))

# B-roll search terms by content category
BROLL_TERMS: dict[str, list[str]] = {
    "beauty": ["skincare routine", "bathroom mirror", "serum application", "glowing skin", "morning routine"],
    "skincare": ["skincare routine", "moisturizer application", "bathroom vanity", "glowing skin", "face wash"],
    "lifestyle": ["cozy home", "morning coffee", "aesthetic desk", "apartment lifestyle", "city walk"],
    "wellness": ["yoga morning", "smoothie making", "journaling", "sunlight window", "walking outdoors"],
    "organization": ["clean desk", "organized closet", "satisfying organization", "storage solutions", "minimalist home"],
    "fashion": ["fashion flatlay", "aesthetic outfit", "mirror selfie aesthetic", "shopping bag", "accessories"],
    "dorm": ["dorm room aesthetic", "college lifestyle", "small space organization", "dorm decor", "study desk"],
    "budget": ["amazon package", "unboxing", "budget finds", "thrift shopping", "affordable finds"],
    "bridge": ["lifestyle aesthetic", "morning routine", "cozy apartment", "daily life", "product flatlay"],
    "gadgets": ["tech setup", "useful gadget", "product unboxing", "desk setup", "cool product"],
    "wellness_fitness": ["workout motivation", "gym aesthetic", "healthy meal prep", "running outdoors", "fitness routine"],
}


def _broll_terms(content_category: str) -> list[str]:
    return BROLL_TERMS.get(content_category, BROLL_TERMS["bridge"])


def _url(path: str) -> str:
    return f"{_BASE_URL.rstrip('/')}/{path.lstrip('/')}"


def is_mpt_running() -> bool:
    try:
        r = requests.get(_url("/ping"), timeout=5)
        return r.status_code == 200
    except Exception:
        return False


@retry(max_attempts=3, delay=5.0)
def submit_video(
    script: str,
    subject: str,
    content_category: str = "bridge",
    voice_name: str = "en-US-JennyNeural",
    video_script_prompt: str = "",
) -> str:
    """Submit a video generation task. Returns task_id."""
    terms = _broll_terms(content_category)

    payload = {
        "video_subject": subject,
        "video_script": script,
        "video_terms": terms,
        "video_aspect": "9:16",
        "video_source": "pexels",
        "video_concat_mode": "random",
        "video_transition_mode": "FadeIn",
        "video_clip_duration": 3,
        "video_count": 1,
        "voice_name": voice_name,
        "voice_rate": 0.95,
        "voice_volume": 1.0,
        "bgm_type": "random",
        "bgm_volume": 0.10,
        "subtitle_enabled": True,
        "subtitle_position": "bottom",
        "font_name": "MicrosoftYaHeiBold.ttc",
        "text_fore_color": "#FFFFFF",
        "text_background_color": True,
        "font_size": 72,
        "stroke_color": "#000000",
        "stroke_width": 1.8,
        "n_threads": 2,
        "paragraph_number": 1,
        "video_script_prompt": video_script_prompt or (
            "Write like a real TikTok creator talking to camera. "
            "Casual, first-person, conversational. Sound like you're telling a friend "
            "about a discovery, not writing an advertisement."
        ),
    }

    log.info("Submitting video to MPT: subject=%r, voice=%s", subject, voice_name)
    r = requests.post(_url("/v1/video/videos"), json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()

    if data.get("status") != 200:
        raise RuntimeError(f"MPT rejected request: {data.get('message')}")

    task_id = data["data"]["task_id"]
    log.info("MPT task created: %s", task_id)
    return task_id


def poll_task(task_id: str, poll_interval: int = 10) -> dict:
    """
    Poll until task is complete or failed. Returns final task data dict.
    Raises RuntimeError on failure or timeout.
    """
    deadline = time.time() + _TIMEOUT
    log.info("Polling MPT task %s (timeout=%ds)...", task_id, _TIMEOUT)

    while time.time() < deadline:
        r = requests.get(_url(f"/v1/video/tasks/{task_id}"), timeout=15)
        r.raise_for_status()
        data = r.json().get("data", {})
        state = data.get("state", 0)
        progress = data.get("progress", 0)

        log.info("  Task %s — state=%s progress=%s%%", task_id, state, progress)

        if state == 2:  # complete
            return data
        if state in (3, 4):  # failed or stopped
            raise RuntimeError(f"MPT task {task_id} ended with state={state}")

        time.sleep(poll_interval)

    raise TimeoutError(f"MPT task {task_id} did not complete within {_TIMEOUT}s")


def download_video(task_data: dict, task_id: str) -> Optional[Path]:
    """
    Download the final video from MPT task data.
    Returns local Path where video was saved.
    """
    videos = task_data.get("combined_videos") or task_data.get("videos") or []
    if not videos:
        log.error("No video URLs in MPT task data for %s", task_id)
        return None

    video_url = videos[0]
    out_path = videos_dir() / f"{task_id}.mp4"

    log.info("Downloading video from %s → %s", video_url, out_path)

    # MPT serves videos locally — handle both http URLs and local paths
    if video_url.startswith("http"):
        r = requests.get(video_url, stream=True, timeout=60)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        # Local file path returned by MPT
        src = Path(video_url)
        if src.exists():
            shutil.copy2(src, out_path)
        else:
            log.error("MPT returned local path that doesn't exist: %s", video_url)
            return None

    log.info("Video saved: %s (%.1f MB)", out_path, out_path.stat().st_size / 1_048_576)
    return out_path


def generate_video(
    script: str,
    subject: str,
    content_category: str = "bridge",
    voice_name: str = "en-US-JennyNeural",
    video_script_prompt: str = "",
) -> tuple[str, Path]:
    """
    Full flow: submit → poll → download.
    Returns (task_id, local_video_path).
    """
    if not is_mpt_running():
        raise ConnectionError(
            "MoneyPrinterTurbo is not running at "
            f"{_BASE_URL}. Start it with: cd MoneyPrinterTurbo && python main.py"
        )

    task_id = submit_video(script, subject, content_category, voice_name, video_script_prompt)
    task_data = poll_task(task_id)
    video_path = download_video(task_data, task_id)

    if video_path is None:
        raise RuntimeError(f"Video download failed for task {task_id}")

    return task_id, video_path
