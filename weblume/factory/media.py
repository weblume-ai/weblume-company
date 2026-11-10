"""Real photos and footage for a factory site, all free for commercial use: the client's own photos first, then
Pexels (PEXELS_API_KEY), Pixabay (PIXABAY_API_KEY, photos and videos) and Openverse (photos, no key, commercial
licenses only). A video becomes WebP frames for the scroll hero, like Loopie (desktop + phone crops).
Every downloaded file is credited in CREDITS.md inside the site."""
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


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "weblume-factory"}), timeout=30) as r:
        return json.loads(r.read())


def _key(name: str) -> str:
    return os.getenv(name, "").strip()


VAGUE = {"warm", "delicious", "making", "process", "close", "closeup", "beautiful", "fresh", "tasty", "cozy", "modern", "luxury",
         "with", "over", "into", "from", "that", "this", "very", "best", "food", "photo", "shot", "view", "style", "inside", "people",
         # places say where, not what: "egyptian cafe" must not bring the pyramids
         "egypt", "egyptian", "cairo", "saudi", "arabia", "arabic", "arab", "riyadh", "jeddah", "middle", "east", "eastern", "traditional", "local"}


def _words(text: str) -> set:
    import re
    return {w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 2 and w not in VAGUE}


DISHES = {"kunafa", "knafeh", "basbousa", "baklava", "qatayef", "dessert", "desserts", "pastry", "pastries", "cake", "cakes", "sweets",
          "chocolate", "waffle", "waffles", "crepe", "pancake", "cookies", "donut", "icecream", "coffee", "espresso", "latte", "cappuccino",
          "tea", "juice", "smoothie", "kebab", "kabab", "shawarma", "grill", "grilled", "barbecue", "bbq", "steak", "meat", "lamb", "chicken",
          "rice", "kabsa", "mandi", "biryani", "falafel", "hummus", "bread", "pizza", "burger", "sandwich", "salad", "soup", "fish", "seafood",
          "restaurant", "cafe", "bakery", "dish", "meal", "plate", "tajine", "tagine", "stew", "pasta", "noodles", "sushi", "dates"}
SEASONAL = {"christmas", "xmas", "halloween", "easter", "valentine", "santa", "thanksgiving", "pumpkin"}


def _relevant(tags: str, query: str) -> bool:
    """A stock search engine fills a long query with anything (a scrapyard for "nutella", a rose for "rose water
    qatayef"): a hit counts when its tags share a dish word with the query, or two real words; never a holiday photo."""
    t, q = _words(tags), _words(query)
    if t & SEASONAL and not q & SEASONAL:
        return False
    shared = t & q
    return bool(shared & DISHES) or len(shared) >= 2


def _queries(query: str) -> list[str]:
    """The model's query, then its first three real words: long queries find less and worse."""
    short = " ".join([w for w in query.lower().split() if w in _words(query)][:3])
    return list(dict.fromkeys(q for q in (query[:100], short) if q))


def _find_photo(query: str, n: int = 0) -> tuple[str, str]:
    """(image url, credit line) from the first source that has one, or ('', '')."""
    q = urllib.parse.urlencode
    if _key("PEXELS_API_KEY"):
        try:
            ph = _pexels("/v1/search?" + q({"query": query, "per_page": n + 1, "orientation": "landscape"}))["photos"][n]
            return ph["src"]["large2x"], f"photo by {ph['photographer']} on Pexels ({ph['url']})"
        except Exception:
            pass
    if _key("PIXABAY_API_KEY"):
        try:
            for qq in _queries(query):
                hits = [h for h in _get_json("https://pixabay.com/api/?" + q({"key": _key("PIXABAY_API_KEY"), "q": qq, "image_type": "photo",
                                                                            "orientation": "horizontal", "safesearch": "true", "per_page": 20}))["hits"]
                        if _relevant(h.get("tags", ""), query)]
                if len(hits) > n:
                    return hits[n]["largeImageURL"], f"photo by {hits[n]['user']} on Pixabay ({hits[n]['pageURL']})"
        except Exception:
            pass
    try:  # Openverse: no key needed; only licenses that allow commercial use
        # their license filter times out (504), so filter here: no "nc" (non-commercial) licenses, no "nd" (no edits: we crop)
        found = _get_json("https://api.openverse.org/v1/images/?" + q({"q": query[:100], "page_size": 20}))["results"]
        r = [x for x in found if not {"nc", "nd"} & set(str(x.get("license", "")).split("-")) and (x.get("width") or 0) >= 1000
             and _relevant(" ".join([x.get("title") or ""] + [t.get("name", "") for t in x.get("tags") or []]), query)][n]
        lic = f"{r['license'].upper()} {r.get('license_version') or ''}".strip()
        return r["url"], f"'{r.get('title') or 'photo'}' by {r.get('creator') or 'unknown'}, {lic}, via Openverse ({r.get('foreign_landing_url') or r['url']})"
    except Exception:
        return "", ""


def photo(query: str, out: Path, dest: Path, credits: list, n: int = 0) -> str:
    """The n-th free photo for a search, saved as WebP in the site. '' when none."""
    if not query:
        return ""
    url, credit = _find_photo(query, n)
    if not url:
        return ""
    try:
        tmp = _download(url, out.with_suffix(".src"))
        _webp(tmp, out)
        tmp.unlink()
    except Exception:
        return ""
    credits.append(f"- {_rel(out, dest)}: {credit}")
    return _rel(out, dest)


def _find_video(query: str) -> tuple[str, str]:
    """(mp4 url 1280-1920 wide, credit line): Pexels, then Pixabay."""
    q = urllib.parse.urlencode
    if _key("PEXELS_API_KEY"):
        try:
            for v in _pexels("/videos/search?" + q({"query": query, "per_page": 5, "orientation": "landscape"})).get("videos", []):
                files = sorted((f for f in v["video_files"] if f.get("file_type") == "video/mp4" and 1280 <= (f.get("width") or 0) <= 1920),
                               key=lambda f: f["width"])
                if files and v.get("duration", 0) >= 5:
                    return files[0]["link"], f"video by {v['user']['name']} on Pexels ({v['url']})"
        except Exception:
            pass
    if _key("PIXABAY_API_KEY"):
        try:
            for qq in _queries(query):
                for h in _get_json("https://pixabay.com/api/videos/?" + q({"key": _key("PIXABAY_API_KEY"), "q": qq,
                                                                           "safesearch": "true", "per_page": 20}))["hits"]:
                    f = h["videos"].get("medium") or h["videos"].get("large")
                    if f and f.get("url") and (f.get("width") or 0) >= 1280 and h.get("duration", 0) >= 5 and _relevant(h.get("tags", ""), query):
                        return f["url"], f"video by {h['user']} on Pixabay ({h['pageURL']})"
        except Exception:
            pass
    return "", ""


def footage(query: str, dest: Path, credits: list, log=print) -> dict:
    """A free video -> frames-d (1280 wide) and frames-m (720 wide, portrait crop) + a short MP4 and a poster."""
    if not query:
        return {}
    url, credit = _find_video(query)
    if not url:
        return {}
    try:
        import imageio_ffmpeg
        ff, a = imageio_ffmpeg.get_ffmpeg_exe(), dest / "assets"
        src = _download(url, a / "source.mp4")
        log(f"   فيديو: {credit}")
        run = lambda *args: subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", *args], check=True, timeout=600)
        (a / "frames-d").mkdir(parents=True, exist_ok=True)
        (a / "frames-m").mkdir(parents=True, exist_ok=True)
        run("-t", "7", "-i", str(src), "-vf", "fps=18,scale=1280:-2", "-c:v", "libwebp", "-quality", "68", str(a / "frames-d" / "%03d.webp"))
        run("-t", "7", "-i", str(src), "-vf", "fps=18,crop=ih*9/16:ih,scale=720:-2", "-c:v", "libwebp", "-quality", "66", str(a / "frames-m" / "%03d.webp"))
        run("-ss", "1", "-t", "8", "-i", str(src), "-an", "-vf", "scale=1280:-2", "-c:v", "libx264", "-crf", "28", "-preset", "veryfast",
            "-movflags", "+faststart", str(a / "clip.mp4"))
        run("-ss", "2", "-i", str(src), "-frames:v", "1", "-c:v", "libwebp", "-quality", "75", str(a / "poster.webp"))
        src.unlink()
        credits.append(f"- assets/frames-*, clip.mp4, poster.webp: {credit}")
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
    kind = str(data.get("kind") or "")
    topic = lambda query: query if not query or kind in query.lower() else f"{query} {kind}"  # "interior" alone finds any interior
    m.update(footage(topic(q.get("video", "")), dest, credits, log))
    pick = lambda i, query, name: own_rel[i] if i < len(own_rel) else photo(topic(query), dest / "assets" / "img" / f"{name}.webp", dest, credits)
    # the place's own footage beats a stock photo found by keywords: its still frame is the hero photo
    m["heroImg"] = own_rel[0] if own_rel else m.get("poster") or pick(0, q.get("hero", ""), "hero")
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
    if not m.get("frames"):
        data["review"].append("مفيش فيديو للهيرو: حط PIXABAY_API_KEY في ملف .env (مجاني من pixabay.com/api/docs) أو ابعت فيديو للمكان")
    swap(data)
    if credits:
        data["credits"] = "CREDITS.md"  # the footer links it: CC BY photos need visible credit
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "CREDITS.md").write_text("# Photo and video credits\n\nAll free for commercial use: Pexels, Pixabay, or Openverse with a commercial license.\n\n" + "\n".join(credits) + "\n", encoding="utf-8")


def swap(data: dict):
    """A piece whose media didn't come is replaced by one that looks finished without it, so nothing shows empty."""
    m, ps = data.get("media", {}), data["pieces"]
    has_items = sum(bool(i.get("img")) for c in data.get("menu") or [] for i in c.get("items") or [])
    photo = bool(m.get("heroImg"))
    rules = {"hero-frames": m.get("frames") and "" or ("hero-split" if photo else "hero-waterline"),
             "hero-split": "" if photo else "hero-waterline", "hero-name-photo": "" if photo else "hero-waterline",
             "hero-card-room": "" if photo else "hero-waterline", "hero-film-title": "" if photo or m.get("video") else "hero-waterline",
             "menu-rows": "" if has_items >= 4 else "menu-cols", "menu-tiles": "" if has_items >= 4 else "menu-cols",
             "menu-sticky-photo": "" if photo or m.get("about") else "menu-cols",
             "menu-flip": "" if has_items >= 4 else "menu-cols", "menu-polaroid": "" if has_items >= 4 else "menu-cols",
             "hero-arch": "" if photo else "hero-waterline", "hero-words": "" if photo else "hero-waterline",
             "hero-layers": "" if photo and len(m.get("gallery") or []) >= 2 else ("hero-split" if photo else "hero-waterline")}
    data["pieces"] = [rules.get(p) or p for p in ps]
    if m.get("frames"):  # footage came: the scroll-played hero (Loopie's signature) is the strongest opening
        data["pieces"] = ["hero-frames" if p.startswith("hero-") else p for p in data["pieces"]]
    for p, ok in (("gallery-track", len(m.get("gallery") or []) >= 3), ("gallery-sheet", len(m.get("gallery") or []) >= 3),
                  ("gallery-stack", len(m.get("gallery") or []) >= 3), ("features-bento", len(data.get("features") or []) >= 2),
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
