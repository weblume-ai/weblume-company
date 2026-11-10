"""The owner's photos and videos for the next site, sent from the dashboard. They wait in output/uploads/inbox until a
factory build takes them (they then move next to that site, so the next build starts empty)."""
import base64
import re
import shutil
from datetime import datetime

from .config import OUTPUT_DIR

INBOX = OUTPUT_DIR / "uploads" / "inbox"
OK = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm", ".m4v"}


def save(name: str, data: str) -> dict:
    ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""
    if ext not in OK:
        raise ValueError("ابعت صور (jpg, png, webp) أو فيديو (mp4, mov, webm) بس.")
    raw = base64.b64decode(data.split(",", 1)[-1], validate=False)
    if len(raw) < 1000:
        raise ValueError("الملف فاضي أو بايظ.")
    INBOX.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.-]+", "-", name.rsplit(".", 1)[0])[:40] or "file"
    out = INBOX / f"{datetime.now():%H%M%S%f}-{safe}{ext}"  # the time keeps the upload order
    out.write_bytes(raw)
    return {"saved": out.name, "inbox": listing()}


def listing() -> list[str]:
    return sorted(p.name for p in INBOX.iterdir()) if INBOX.exists() else []


def clear() -> dict:
    shutil.rmtree(INBOX, ignore_errors=True)
    return {"inbox": []}


def take(site_name: str):
    """The inbox for this build, or None. The files move to output/uploads/<site> afterwards (see done)."""
    return INBOX if listing() else None


def done(site_name: str):
    if INBOX.exists() and listing():
        dest = OUTPUT_DIR / "uploads" / f"{datetime.now():%Y-%m-%d_%H%M}_{re.sub(r'[^\w-]+', '-', site_name)[:30]}"
        shutil.move(str(INBOX), str(dest))
