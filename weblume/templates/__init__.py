"""Ready site templates for Karim.

cafe   = the Loopie design (a whole folder): Karim writes only the client's content as JSON, the code builds the site.
clinic, shop, game, fresh = single pages Karim edits (fresh: a blank page shaped by an inspiration direction);
the motion kit is injected after him.
"""
import json
import re
import shutil
import urllib.request
from pathlib import Path

from .. import logo

DIR = Path(__file__).parent
CSS_MARK, JS_MARK = "<!--WEBLUME:MOTION_CSS-->", "<!--WEBLUME:MOTION_JS-->"
FOLDER = {"cafe"}  # templates that are a site folder filled from JSON
KINDS = {  # template -> words that pick it (Arabic + English)
    "cafe": ["café", "cafe", "coffee", "كافيه", "كافية", "قهوة", "مقهى"],
    "fresh": ["restaurant", "bakery", "food", "kitchen", "pizza", "burger", "portfolio", "agency", "event", "landing",
              "مطعم", "مخبز", "حلويات", "أكل", "اكل", "كشري", "مشويات", "بورتفوليو", "أعمالي", "شركة", "ايفنت", "فرح"],
    "game": ["game", "gaming", "لعبة", "ألعاب", "العاب"],
    "clinic": ["clinic", "doctor", "dental", "dentist", "salon", "spa", "gym", "lawyer", "school", "center", "service",
               "عيادة", "دكتور", "أسنان", "اسنان", "صالون", "جيم", "محامي", "مدرسة", "مركز", "خدمات"],
    "shop": ["shop", "store", "boutique", "brand", "clothes", "gift", "perfume", "متجر", "محل", "براند", "هدايا",
             "ملابس", "عطور", "اكسسوارات"],
}


def pick(text: str) -> str:
    """Which template fits the request; anything we have no ready design for gets a fresh design ("fresh")."""
    t = text.lower()
    scores = {k: sum(w in t for w in words) for k, words in KINDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "fresh"


def load(kind: str) -> str:
    """What Karim starts from: the page to edit, or for a folder template the example content to copy the shape of."""
    if kind in FOLDER:
        return (DIR / kind / "example-data.js").read_text(encoding="utf-8")
    return (DIR / f"{kind}.html").read_text(encoding="utf-8")


def guide(kind: str = "") -> str:
    return (DIR / (f"{kind}/GUIDE.md" if kind in FOLDER else "GUIDE.md")).read_text(encoding="utf-8")


def _image_paths(node):
    """Every local image path in the content (keys img / src), as (holder, key)."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("img", "src") and isinstance(v, str) and not v.startswith(("http://", "https://")):
                yield node, k
            else:
                yield from _image_paths(v)
    elif isinstance(node, list):
        for v in node:
            yield from _image_paths(v)


def drop_unsourced(data: dict, source: str) -> list[str]:
    """Prices and opening hours must come from the owner's own request; anything else was made up and is removed."""
    said = set(re.findall(r"\d+(?:\.\d+)?", source.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))))
    dropped = []
    for cat in data.get("menu") or []:
        for item in (cat.get("items") or []) if isinstance(cat, dict) else []:
            p = item.get("price") if isinstance(item, dict) else ""
            num = re.search(r"\d+(?:\.\d+)?", str(p).translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")))
            if p not in ("", None) and (not num or f"{float(num.group()):g}" not in {f"{float(x):g}" for x in said}):
                item["price"] = ""
                dropped.append("price")
    if data.get("hours") and not re.search(r"\d{1,2}[:٫.]\d{2}|24\s*(h|ساعة|hours)|\b\d{1,2}\s*(am|pm|ص|م)\b|الساعة|ساعات", source, re.I):
        data.pop("hours")
        dropped.append("hours")
    return dropped


def build_site(kind: str, data: dict, dest: Path) -> int:
    """Copy a folder template to dest and write the client's content as data.js. Returns how many image paths it fixed."""
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(DIR / kind, dest, ignore=shutil.ignore_patterns("example-data.js", "GUIDE.md"))
    fixed = 0
    for holder, key in list(_image_paths(data)):  # a made-up path would leave an empty frame
        if not (dest / holder[key]).is_file():
            holder[key] = "assets/img/menu-coffee.webp" if key == "img" else "assets/img/mood-cup.webp"
            fixed += 1
    if not data.get("logo"):  # no logo from the client yet: a clean type logo until he sends the real one
        colors = data.get("colors") or {}
        (dest / "assets" / "img" / "logo.svg").write_text(
            logo.make(data.get("word") or data.get("name") or "Brand", colors.get("accent", "#141414"), colors.get("ink", "#141414")), encoding="utf-8")
        page = dest / "index.html"
        page.write_text(page.read_text(encoding="utf-8").replace("assets/img/logo.webp", "assets/img/logo.svg"), encoding="utf-8")
        data["logo"] = "assets/img/logo.svg"
    if not data.get("drinks"):  # the drinks scene reads the first drink on load; an empty list breaks the page
        data["drinks"] = [{"mood": "مستعجل", "name": "إسبريسو", "desc": "", "img": "assets/img/drink-esp.webp", "ratio": "800/550",
                           "s": .62, "bg": "#FFFFFF", "disc": (data.get("colors") or {}).get("accent", "#EBB81F"), "fg": "#141210"}]
    data.setdefault("demo", True)
    (dest / "data.js").write_text("window.CAFE = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
    return fixed


_IMG = re.compile(r'<img\b[^>]*\bsrc="(https?://[^"]+)"[^>]*>', re.I)


def _loads(url: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-1023"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status < 400 and r.headers.get("Content-Type", "").startswith("image/")
    except Exception:
        return False


def fix_broken_images(html: str, check=_loads) -> tuple[str, int]:
    """Models make up photo links. Free stock (Pexels…) is fine; a link that doesn't load becomes a labeled
    placeholder for a real photo. Returns (html, how many were dead)."""
    seen = {}

    def ph(m):
        url = m.group(1)
        if url not in seen:
            seen[url] = check(url)
        if seen[url]:
            return m.group(0)
        tag = m.group(0)
        alt = re.search(r'\balt="([^"]*)"', tag)
        cls = re.search(r'\bclass="([^"]*)"', tag)
        classes = " ".join(dict.fromkeys(["ph", *(cls.group(1).split() if cls else [])]))
        label = ((alt.group(1) + " · ") if alt and alt.group(1) else "") + "صورة حقيقية من العميل"
        return f'<div class="{classes}" data-label="{label}"></div>'

    out = _IMG.sub(ph, html)
    return out, sum(not ok for ok in seen.values())


def claims_to_check(text: str) -> list[str]:
    """Things that are often invented: the owner must confirm them with the client before the site goes out."""
    plain = re.sub(r"<[^>]+>", " ", text)
    found = []
    if re.search(r"آراء|قالوا عن|testimonial|reviews?\b|what (our )?(customers|clients) say", plain, re.I):
        found.append("a reviews section (keep only real reviews from the client)")
    if "data-count=" in text or re.search(r"\d(\.\d)?\s*★|★\s*\d", plain):
        found.append("numbers / ratings (years, customers, Google rating)")
    return found


def inject_motion(html: str) -> str:
    """Put the motion kit into the page, at the markers if Karim kept them, else before </head> and </body>."""
    css = "<style>/* wl-motion-kit */\n" + (DIR / "motion.css").read_text(encoding="utf-8") + "</style>"
    js = "<script>\n" + (DIR / "motion.js").read_text(encoding="utf-8") + "</script>"
    if "/* wl-motion-kit */" in html:  # already injected (e.g. the draft went through twice)
        return html
    for mark, code, before in ((CSS_MARK, css, "</head>"), (JS_MARK, js, "</body>")):
        if mark in html:
            html = html.replace(mark, code, 1)
        elif before in html.lower():
            i = html.lower().rfind(before)
            html = html[:i] + code + "\n" + html[i:]
        else:
            html += code
    return html
