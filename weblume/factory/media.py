"""Real photos and footage for a factory site: the client's own photos first, then Pexels (free for commercial use,
needs PEXELS_API_KEY in .env). A video becomes WebP frames for the scroll hero, like Loopie (desktop + phone crops).
Every Pexels file is credited in CREDITS.md inside the site."""
import json
import os
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.pexels.com"
EXT = (".jpg", ".jpeg", ".png", ".webp")


def _pexels(path: str) -> dict:
    req = urllib.request.Request(API + path, headers={"Authorization": os.getenv("PEXELS_API_KEY", "").strip(), "User-Agent": "weblume-factory"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _download(url: str, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=120) as r:
        out.write_bytes(r.read())
    return out


def _webp(src: Path, out: Path, width: int = 1400) -> Path:
    """Resize and compress a photo to WebP."""
    from PIL import Image
    with Image.open(src) as im:
        im = im.convert("RGB")
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)))
        out.parent.mkdir(parents=True, exist_ok=True)
        im.save(out, "WEBP", quality=78)
    return out


def _rel(out: Path, dest: Path) -> str:
    return out.relative_to(dest).as_posix()


def photo(query: str, out: Path, dest: Path, credits: list, n: int = 0) -> str:
    """The n-th Pexels photo for a search, saved as WebP in the site. '' when none."""
    if not query or not os.getenv("PEXELS_API_KEY", "").strip():
        return ""
    try:
        res = _pexels("/v1/search?" + urllib.parse.urlencode({"query": query, "per_page": n + 1, "orientation": "landscape"}))
        ph = res["photos"][n]
        tmp = _download(ph["src"]["large2x"], out.with_suffix(".src"))
        _webp(tmp, out)
        tmp.unlink()
        credits.append(f"- {_rel(out, dest)}: photo by {ph['photographer']} on Pexels ({ph['url']})")
        return _rel(out, dest)
    except Exception:
        return ""


def footage(query: str, dest: Path, credits: list, log=print) -> dict:
    """A Pexels video → frames-d (1280 wide) and frames-m (720 wide, portrait crop) + a short MP4 and a poster."""
    if not query or not os.getenv("PEXELS_API_KEY", "").strip():
        return {}
    try:
        res = _pexels("/videos/search?" + urllib.parse.urlencode({"query": query, "per_page": 5, "orientation": "landscape"}))
        for v in res.get("videos", []):
            files = sorted((f for f in v["video_files"] if f.get("file_type") == "video/mp4" and 1280 <= (f.get("width") or 0) <= 1920),
                           key=lambda f: f["width"])
            if files and v.get("duration", 0) >= 5:
                break
        else:
            return {}
        import imageio_ffmpeg
        ff, a = imageio_ffmpeg.get_ffmpeg_exe(), dest / "assets"
        src = _download(files[0]["link"], a / "source.mp4")
        log(f"   فيديو: {v['url']}")
        run = lambda *args: subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", *args], check=True, timeout=600)
        (a / "frames-d").mkdir(parents=True, exist_ok=True)
        (a / "frames-m").mkdir(parents=True, exist_ok=True)
        run("-t", "7", "-i", str(src), "-vf", "fps=18,scale=1280:-2", "-c:v", "libwebp", "-quality", "68", str(a / "frames-d" / "%03d.webp"))
        run("-t", "7", "-i", str(src), "-vf", "fps=18,crop=ih*9/16:ih,scale=720:-2", "-c:v", "libwebp", "-quality", "66", str(a / "frames-m" / "%03d.webp"))
        run("-ss", "1", "-t", "8", "-i", str(src), "-an", "-vf", "scale=1280:-2", "-c:v", "libx264", "-crf", "28", "-preset", "veryfast",
            "-movflags", "+faststart", str(a / "clip.mp4"))
        run("-ss", "2", "-i", str(src), "-frames:v", "1", "-c:v", "libwebp", "-quality", "75", str(a / "poster.webp"))
        src.unlink()
        credits.append(f"- assets/frames-*, clip.mp4, poster.webp: video by {v['user']['name']} on Pexels ({v['url']})")
        n = len(list((a / "frames-d").glob("*.webp")))
        return {"frames": {"d": "assets/frames-d/", "m": "assets/frames-m/", "n": n}, "video": "assets/clip.mp4", "poster": "assets/poster.webp"}
    except Exception as e:
        log(f"   الفيديو مانفعش: {e}")
        return {}


def fill(data: dict, dest: Path, client_photos: Path | None = None, log=print):
    """Put media paths into data['media'], downloading into dest/assets. Client photos come first."""
    q, m, credits = data.get("media_query") or {}, data.setdefault("media", {}), []
    own = sorted(p for p in (client_photos.iterdir() if client_photos and client_photos.is_dir() else []) if p.suffix.lower() in EXT)
    own_rel = [_rel(_webp(p, dest / "assets" / "own" / f"{i + 1:02d}.webp"), dest) for i, p in enumerate(own)]
    if own_rel:
        log(f"   {len(own_rel)} صورة من العميل")
    m.update(footage(q.get("video", ""), dest, credits, log))
    pick = lambda i, query, name: own_rel[i] if i < len(own_rel) else photo(query, dest / "assets" / "img" / f"{name}.webp", dest, credits)
    m["heroImg"] = pick(0, q.get("hero", ""), "hero")
    about = pick(1, q.get("about", ""), "about")
    if about:
        m["about"] = {"src": about, "alt": data.get("name", "")}
    gallery = [pick(2 + i, g, f"gallery-{i + 1}") for i, g in enumerate((q.get("gallery") or [])[:5])]
    m["gallery"] = [{"src": g, "alt": data.get("name", "")} for g in gallery if g]
    k = 0
    for cat in data.get("menu") or []:  # a photo for the first items, so cards never stay empty
        for it in cat.get("items") or []:
            if k < 12 and it.get("photo"):
                it["img"] = photo(it["photo"], dest / "assets" / "img" / f"item-{k + 1}.webp", dest, credits)
                k += 1
    if not os.getenv("PEXELS_API_KEY", "").strip() and not own_rel:
        data["review"].append("مفيش صور: حط PEXELS_API_KEY في ملف .env (مجاني من pexels.com/api) أو ابعت صور المكان")
    swap(data)
    if credits:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "CREDITS.md").write_text("# Photo and video credits\n\nAll from Pexels (free to use, Pexels license).\n\n" + "\n".join(credits) + "\n", encoding="utf-8")


def swap(data: dict):
    """A piece whose media didn't come is replaced by one that looks finished without it, so nothing shows empty."""
    m, ps = data.get("media", {}), data["pieces"]
    has_items = sum(bool(i.get("img")) for c in data.get("menu") or [] for i in c.get("items") or [])
    photo = bool(m.get("heroImg"))
    rules = {"hero-frames": m.get("frames") and "" or ("hero-split" if photo else "hero-waterline"),
             "hero-split": "" if photo else "hero-waterline", "hero-name-photo": "" if photo else "hero-waterline",
             "hero-card-room": "" if photo else "hero-waterline", "hero-film-title": "" if photo or m.get("video") else "hero-waterline",
             "menu-rows": "" if has_items >= 4 else "menu-cols", "menu-tiles": "" if has_items >= 4 else "menu-cols",
             "menu-sticky-photo": "" if photo or m.get("about") else "menu-cols"}
    data["pieces"] = [rules.get(p) or p for p in ps]
    for p, ok in (("gallery-track", len(m.get("gallery") or []) >= 3), ("gallery-sheet", len(m.get("gallery") or []) >= 3),
                  ("invite-video", m.get("video") or m.get("poster"))):
        if p in data["pieces"] and not ok:
            data["pieces"].remove(p)


def drop_broken(data: dict, issues: list[str]):
    """After the review: remove any media path the browser couldn't load."""
    bad = {i.split("BROKEN ", 1)[1].split(" ", 1)[0] for i in issues if i.startswith("BROKEN ")}
    m = data.get("media", {})
    m["gallery"] = [g for g in m.get("gallery", []) if g["src"] not in bad]
    for cat in data.get("menu") or []:
        for it in cat.get("items") or []:
            if it.get("img") in bad:
                it.pop("img")
