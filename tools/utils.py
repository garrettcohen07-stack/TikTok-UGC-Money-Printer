"""
Shared utilities: env loading, SQLite DB setup, logging, retry helpers.
"""
import json
import logging
import os
import sqlite3
import time
from datetime import datetime
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (two levels up from tools/)
_PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("ugc")


# ── Env helpers ──────────────────────────────────────────────────────────────

def require_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return val


def get_env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def use_sqlite() -> bool:
    return get_env("USE_SQLITE", "true").lower() == "true"


# ── Paths ─────────────────────────────────────────────────────────────────────

def project_root() -> Path:
    return _PROJECT_ROOT


def videos_dir() -> Path:
    d = Path(get_env("VIDEO_OUTPUT_DIR", ".tmp/videos"))
    if not d.is_absolute():
        d = _PROJECT_ROOT / d
    d.mkdir(parents=True, exist_ok=True)
    return d


def scripts_dir() -> Path:
    d = Path(get_env("SCRIPTS_OUTPUT_DIR", ".tmp/scripts"))
    if not d.is_absolute():
        d = _PROJECT_ROOT / d
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── SQLite DB ─────────────────────────────────────────────────────────────────

def _db_path() -> Path:
    p = Path(get_env("SQLITE_DB_PATH", ".tmp/database.db"))
    if not p.is_absolute():
        p = _PROJECT_ROOT / p
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def get_db() -> sqlite3.Connection:
    db = sqlite3.connect(str(_db_path()))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db


def init_db() -> None:
    """Create all tables if they don't exist."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS videos (
            id              TEXT PRIMARY KEY,
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now')),
            status          TEXT NOT NULL DEFAULT 'draft',
            content_category TEXT,
            transition_phase INTEGER DEFAULT 1,
            script_id       TEXT,
            hook_id         TEXT,
            caption         TEXT,
            hashtags        TEXT,
            mpt_task_id     TEXT,
            final_video_path TEXT,
            tiktok_draft_id TEXT,
            tiktok_post_id  TEXT,
            authenticity_score INTEGER,
            compliance_score INTEGER,
            compliance_flags TEXT,
            reviewer_notes  TEXT,
            scheduled_post_time TEXT,
            posted_at       TEXT,
            ab_test_group   TEXT,
            voice_name      TEXT,
            video_params    TEXT
        );

        CREATE TABLE IF NOT EXISTS scripts (
            id              TEXT PRIMARY KEY,
            created_at      TEXT DEFAULT (datetime('now')),
            subject         TEXT NOT NULL,
            hook_line       TEXT,
            body            TEXT NOT NULL,
            cta             TEXT,
            word_count      INTEGER,
            tone            TEXT,
            content_category TEXT,
            product_id      TEXT,
            trend_id        TEXT,
            authenticity_score INTEGER,
            revision_count  INTEGER DEFAULT 0,
            approved        INTEGER DEFAULT 0,
            generation_prompt TEXT
        );

        CREATE TABLE IF NOT EXISTS hooks (
            id              TEXT PRIMARY KEY,
            created_at      TEXT DEFAULT (datetime('now')),
            hook_text       TEXT NOT NULL,
            hook_type       TEXT,
            emotion         TEXT,
            content_category TEXT,
            avg_completion_rate REAL,
            win_rate        REAL,
            use_count       INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS products (
            id              TEXT PRIMARY KEY,
            tiktok_product_id TEXT UNIQUE,
            name            TEXT NOT NULL,
            category        TEXT,
            price_usd       REAL,
            commission_rate REAL,
            affiliate_link  TEXT,
            trending_score  INTEGER,
            audience_fit    TEXT,
            is_active       INTEGER DEFAULT 1,
            last_scraped_at TEXT
        );

        CREATE TABLE IF NOT EXISTS run_log (
            id              TEXT PRIMARY KEY,
            created_at      TEXT DEFAULT (datetime('now')),
            pipeline_run_id TEXT,
            stage           TEXT,
            status          TEXT,
            input_summary   TEXT,
            output_summary  TEXT,
            duration_sec    REAL,
            error           TEXT
        );
    """)
    db.commit()
    db.close()
    log.info("Database initialized at %s", _db_path())


# ── ID generation ─────────────────────────────────────────────────────────────

def new_id() -> str:
    import uuid
    return str(uuid.uuid4())


# ── Persistence helpers ───────────────────────────────────────────────────────

def save_script(script_data: dict) -> str:
    sid = script_data.get("id") or new_id()
    script_data["id"] = sid
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO scripts
            (id, subject, hook_line, body, cta, word_count, tone,
             content_category, authenticity_score, revision_count,
             approved, generation_prompt)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        sid,
        script_data.get("subject", ""),
        script_data.get("hook_line", ""),
        script_data.get("body", ""),
        script_data.get("cta", ""),
        script_data.get("word_count", 0),
        script_data.get("tone", "authentic"),
        script_data.get("content_category", "bridge"),
        script_data.get("authenticity_score"),
        script_data.get("revision_count", 0),
        1 if script_data.get("approved") else 0,
        script_data.get("generation_prompt", ""),
    ))
    db.commit()
    db.close()
    return sid


def save_hook(hook_data: dict) -> str:
    hid = hook_data.get("id") or new_id()
    hook_data["id"] = hid
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO hooks
            (id, hook_text, hook_type, emotion, content_category)
        VALUES (?,?,?,?,?)
    """, (
        hid,
        hook_data.get("hook_text", ""),
        hook_data.get("hook_type", "statement"),
        hook_data.get("emotion", "curiosity"),
        hook_data.get("content_category", "bridge"),
    ))
    db.commit()
    db.close()
    return hid


def save_video(video_data: dict) -> str:
    vid = video_data.get("id") or new_id()
    video_data["id"] = vid
    hashtags = video_data.get("hashtags", [])
    if isinstance(hashtags, list):
        hashtags = json.dumps(hashtags)
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO videos
            (id, status, content_category, transition_phase,
             script_id, hook_id, caption, hashtags,
             mpt_task_id, final_video_path,
             authenticity_score, voice_name, video_params)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        vid,
        video_data.get("status", "draft"),
        video_data.get("content_category", "bridge"),
        video_data.get("transition_phase", 1),
        video_data.get("script_id"),
        video_data.get("hook_id"),
        video_data.get("caption", ""),
        hashtags,
        video_data.get("mpt_task_id"),
        video_data.get("final_video_path"),
        video_data.get("authenticity_score"),
        video_data.get("voice_name", "en-US-JennyNeural"),
        json.dumps(video_data.get("video_params", {})),
    ))
    db.commit()
    db.close()
    return vid


def update_video_status(video_id: str, status: str, **kwargs) -> None:
    db = get_db()
    sets = ["status = ?", "updated_at = datetime('now')"]
    vals = [status]
    for k, v in kwargs.items():
        sets.append(f"{k} = ?")
        vals.append(v)
    vals.append(video_id)
    db.execute(f"UPDATE videos SET {', '.join(sets)} WHERE id = ?", vals)
    db.commit()
    db.close()


# ── Retry decorator ───────────────────────────────────────────────────────────

def retry(max_attempts: int = 3, delay: float = 2.0, backoff: float = 2.0):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            attempt = 0
            wait = delay
            while attempt < max_attempts:
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    log.warning("Attempt %d/%d failed for %s: %s — retrying in %.1fs",
                                attempt, max_attempts, fn.__name__, e, wait)
                    time.sleep(wait)
                    wait *= backoff
        return wrapper
    return decorator


# ── Save output to file ───────────────────────────────────────────────────────

def save_script_file(pipeline_run_id: str, data: dict) -> Path:
    out = scripts_dir() / f"{pipeline_run_id}.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


# ── Transition phase helper ───────────────────────────────────────────────────

def current_transition_phase() -> int:
    return int(get_env("TRANSITION_PHASE", "1"))
