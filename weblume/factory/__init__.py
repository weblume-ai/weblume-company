"""Weblume site factory: ready, tested pieces (from Loopie and Weblume's own sites) + a data file the local model writes
+ real media + an automatic browser review. The model never writes the site's code, only its content and which pieces.

    python -m weblume.factory "اعمل موقع لمطعم مشويات اسمه السفرة في الرياض، واتساب 9665…"

Steps: plan (model → data) → media (client photos, then Pexels) → assemble (pieces + data.js) → review (Playwright) → report.
"""
import json
import os
import re
import shutil
import urllib.request
from pathlib import Path

from ..config import OUTPUT_DIR, ROOT
from .. import inspiration, rules

EXAMPLES = ROOT / "knowledge" / "factory-examples"  # every build; approved ones teach the model (and later train it)


def save_example(request: str, data: dict, folder: Path):
    EXAMPLES.mkdir(parents=True, exist_ok=True)
    keep = {k: data.get(k) for k in ("name", "kind", "style", "tagline", "heroLines", "lede", "about", "together", "invite", "colors", "fonts", "menu", "pieces")}
    (EXAMPLES / f"{folder.name}.json").write_text(json.dumps({"request": request, "approved": False, "data": keep}, ensure_ascii=False, indent=1), encoding="utf-8")


def approve(name: str, ok: bool = True) -> Path:
    """The owner liked this site: it becomes an example the model follows (and a training sample later)."""
    f = EXAMPLES / f"{name}.json"
    ex = json.loads(f.read_text(encoding="utf-8"))
    ex["approved"] = ok
    f.write_text(json.dumps(ex, ensure_ascii=False, indent=1), encoding="utf-8")
    return f


def examples(n: int = 2) -> str:
    """The last approved sites, trimmed, shown to the model as the quality to match."""
    if not EXAMPLES.exists():
        return ""
    good = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(EXAMPLES.glob("*.json"), key=lambda f: f.stat().st_mtime)]
    good = [g for g in good if g.get("approved")][-n:]
    return "\n".join(json.dumps({"request": g["request"], "data": g["data"]}, ensure_ascii=False)[:1800] for g in good)

HERE = Path(__file__).parent
PIECES = HERE / "pieces"
MANIFEST = json.loads((PIECES / "manifest.json").read_text(encoding="utf-8"))
ORDER = ["nav", "hero", "band", "about", "features", "menu", "how", "cta", "gallery", "contact", "footer", "mobile-bar"]  # a piece type's place on the page
LENIS = "https://cdn.jsdelivr.net/npm/lenis@1.1.13/dist/lenis.min.js"
SA = ["الرياض", "جدة", "جده", "الدمام", "مكة", "المدينة", "الخبر", "أبها", "الطائف", "السعودية", "riyadh", "jeddah", "saudi"]
EG = ["القاهرة", "الاسكندرية", "الإسكندرية", "المنصورة", "الجيزة", "طنطا", "مصر", "cairo", "egypt", "alexandria"]

SCHEMA = """{
 "name": "full business name", "word": "one short brand word (for the logo text and the footer)",
 "kind": "restaurant | cafe | sweets | bakery | clinic | shop | gym | salon | company",
 "style": "luxury | bold | simple | playful | heritage | modern",
 "shape": "the shape of photos, cards and buttons: round | arch | sharp | soft | organic (pick what suits the place)",
 "motion": "calm | lively | cinematic (how much the page moves)",
 "blend": "one line: what you took from A, B and C",
 "features": ["2 to 4 real strengths from the request, 2-4 words each (delivery, open late, family hall…); empty if none are known"],
 "tagline": "6 words max", "heroLines": ["2 or 3 short lines, the headline"], "lede": "one sentence under the headline",
 "about": "two sentences: who it's for and why choose it", "together": "a short warm line above the about text",
 "invite": "one short line inviting people to come", "caps": ["3 or 4 one-word scene captions for the hero footage, optional"],
 "colors": {"ink": "#page background: deep (espresso, forest, navy, charcoal) or light (cream, sand, white)", "paper": "#text color, the opposite of ink",
            "accent": "#one brand color (never gold or yellow-gold on a dark page)", "muted": "#soft text color", "surface": "#card color", "onAccent": "#text on accent"},
 "fonts": {"display": "an Arabic Google Font for headings (Alexandria, Lalezar, El Messiri, Reem Kufi Fun, Cairo)", "text": "IBM Plex Sans Arabic or Tajawal"},
 "menu": [{"cat": "category", "items": [{"name": "item", "desc": "ingredients · separated · by dots", "price": "number or empty", "photo": "English photo search words for this exact item"}]}],
 "media_query": {"video": "English search words for a short video of this place's craft (e.g. 'meat grilling on charcoal close up')",
                 "hero": "English words for the hero photo", "about": "English words", "gallery": ["5 English photo searches: interior, food, people at tables…"]},
 "pieces": ["ids from the PIECES list, in page order"],
 "review": ["anything the owner must check before the client sees it: estimated prices, address, photos…"]
}"""


# ------------------------------------------------------------------ plan: the local model writes the content
def _ask_local(prompt: str) -> str:
    """Ollama on this laptop (no daily limit). FACTORY_MODEL picks the model; JSON mode keeps the answer parseable."""
    body = {"model": os.getenv("FACTORY_MODEL", "weblume-factory"), "messages": [{"role": "user", "content": prompt}],
            "format": "json", "stream": False, "options": {"num_ctx": 8192, "temperature": .6}}
    req = urllib.request.Request(os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/") + "/api/chat",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["message"]["content"]


def _ask_cloud(prompt: str) -> str:
    """The free cloud chain (Gemini → Groq → FreeLLM) when the local model can't."""
    from ..config import best_llm
    return best_llm("write").call(prompt)


def plan(request: str, ask=None) -> dict:
    country = "SA" if any(w in request.lower() for w in SA) else "EG" if any(w in request.lower() for w in EG) else ""
    pieces = "\n".join(f"- {k}: {v['type']}, fits {','.join(v['fits'])}, style {','.join(v['style'])}, needs {','.join(v['needs']) or '-'}"
                       for k, v in MANIFEST.items())
    prompt = (f"You write the content of a website for Weblume (a web studio). The client's request:\n\"\"\"{request}\"\"\"\n\n"
              f"Write natural Arabic in the client's dialect ({'Saudi' if country == 'SA' else 'Egyptian' if country == 'EG' else 'simple Arabic'}). "
              "Use every fact the request gives (name, menu, prices, address, WhatsApp, links). When something is missing, write a "
              "realistic placeholder and list it in \"review\". NEVER invent reviews, ratings, customer counts, awards or phone numbers. "
              "Prices you were not given: realistic for the country, and say so in review. Menu: 3 to 5 categories, 4 to 6 items each. "
              "Colors from the business's mood (no gold on black, no gradients). Pick pieces: exactly one nav, one hero, one menu, "
              f"visit, footer-huge and bar; add about-say, gallery-track, invite-video when they help.\n\nPIECES:\n{pieces}\n\n"
              "BLEND THREE AWARD-WINNING SITES into a new look (never copy any of them): take the layout and hero idea from A "
              "(it decides your hero piece and shape), the colours and type from B (your colors and fonts, in this business's mood), "
              "and the motion and section rhythm from C (your motion and the order of pieces). Say what you took in \"blend\".\n"
              f"{inspiration.blend(request)}\n\n"
              + (f"APPROVED EXAMPLES OF WEBLUME SITES (match this quality and voice):\n{examples()}\n\n" if examples() else "") +
              f"Answer with ONE JSON object only, in this shape:\n{SCHEMA}")
    raw = ""
    for fn in ([ask] if ask else [_ask_local, _ask_cloud]):
        try:
            raw = fn(prompt)
            data = rules.extract_json(raw)
            problem = weak(data)
            if not problem:
                return normalize(data, request, country)
            raw = f"rejected: {problem}"  # a weak answer goes to the next (stronger) model
        except Exception as e:  # local model off or confused: next one
            raw = f"{type(e).__name__}: {e}"
    raise RuntimeError(f"The model didn't return usable site data: {raw[:300]}")


def weak(d) -> str:
    """Why the model's content isn't good enough to build on ('' when it is): copy-pasted items, an empty menu, no text."""
    if not isinstance(d, dict) or not d.get("name") or not d.get("menu"):
        return "missing name or menu"
    items = [str(i.get("name", "")).strip() for c in d["menu"] if isinstance(c, dict) for i in c.get("items") or [] if isinstance(i, dict)]
    if len(items) < 6:
        return "menu too short"
    if len(set(items)) < len(items) * .85:
        return "repeated menu items"
    if len(str(d.get("about", ""))) < 40 or not d.get("heroLines"):
        return "missing texts"
    return ""


FONTS_OK = {"Alexandria", "El Messiri", "Lalezar", "Cairo", "Readex Pro", "Tajawal", "IBM Plex Sans Arabic", "Almarai", "Changa"}


def _lum(hexc: str) -> float:
    h = str(hexc).lstrip("#")
    h = "".join(c * 2 for c in h) if len(h) == 3 else h[:6]
    try:
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return -1
    f = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def _contrast(a: str, b: str) -> float:
    x, y = sorted((_lum(a), _lum(b)), reverse=True)
    return (x + .05) / (y + .05)


def _rgb(hexc: str) -> tuple:
    h = str(hexc).lstrip("#")
    h = "".join(ch * 2 for ch in h) if len(h) == 3 else h[:6]
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _shade(hexc: str, f: float) -> str:
    """Lighter (f > 1) or darker (f < 1) version of a color."""
    return "#" + "".join(f"{max(0, min(255, round(v * f + (12 if f > 1 else 0)))):02x}" for v in _rgb(hexc))


def _gold(hexc: str) -> bool:
    import colorsys
    try:
        h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in _rgb(hexc)))
    except ValueError:
        return False
    return 30 / 360 <= h <= 52 / 360 and s > .35 and .35 < l < .8


def palette(c: dict) -> dict:
    """The pieces are built for a dark page with light text: keep the model's mood, fix what would be unreadable."""
    c = {k: v for k, v in (c or {}).items() if isinstance(v, str) and _lum(v) >= 0}
    if _lum(c.get("ink", "")) > .7 and 0 <= _lum(c.get("paper", "#fff")) < .06:  # a light page with dark text: kept, pieces swap roles
        ink, paper = c["ink"], c["paper"]
        surface = c.get("surface") if _lum(c.get("surface", "")) > .55 and _contrast(paper, c.get("surface", "#000")) >= 7 else _shade(ink, .93)
    else:
        ink = c.get("ink") if 0 <= _lum(c.get("ink", "")) < .06 else "#141210"
        paper = c.get("paper") if _lum(c.get("paper", "")) > .8 else "#ffffff"
        surface = c.get("surface") if 0 <= _lum(c.get("surface", "")) < .1 and _contrast(paper, c.get("surface", "#fff")) >= 7 else _shade(ink, 1.6)
    accent = c.get("accent", "")
    if _lum(ink) < .06 and _gold(accent):  # the owner's taste: never gold on dark
        accent = "#c8553d"
    accent = accent if _contrast(accent or "#000", ink) >= 3 else ("#c8553d" if _lum(ink) < .5 else "#a3361f")
    muted = c.get("muted") if _contrast(c.get("muted", ink), ink) >= 4.5 else ("#b9b1a7" if _lum(ink) < .5 else "#5f574d")
    return {"ink": ink, "paper": paper, "accent": accent, "surface": surface, "muted": muted,
            "onAccent": "#141210" if _contrast(accent, "#141210") >= _contrast(accent, "#ffffff") else "#ffffff"}


def normalize(d: dict, request: str, country: str) -> dict:
    """Code, not the model, has the last word: valid pieces in page order, the country's currency, the client's WhatsApp,
    no invented phone numbers, and a review list."""
    d["country"] = country or d.get("country") or "EG"
    d["currency"] = "ر.س" if d["country"] == "SA" else "ج.م"
    d["lang"] = "ar"
    wa = re.search(r"(?:\+|00)?(9665\d{8}|201[0125]\d{8})", request.replace(" ", ""))
    d["whatsapp"] = wa.group(1) if wa else ""
    review = [str(r) for r in d.get("review") or []]
    if not wa:
        review.append("رقم الواتساب: مش موجود في الطلب، زرار الواتساب بيودّي لقسم «زورونا» لحد ما يتحط")
    for k in ("about", "lede", "tagline", "invite", "together"):  # a phone number the model typed is never kept
        if isinstance(d.get(k), str):
            d[k] = re.sub(r"\+?\d[\d\s-]{8,}\d", "", d[k])
    chosen = [p for p in dict.fromkeys(d.get("pieces") or []) if p in MANIFEST]
    for need in ("nav", "visit", "footer-huge", "bar"):
        if need not in chosen:
            chosen.append(need)
    for typ, default in (("hero", "hero-frames"), ("menu", "menu-cols")):
        if not any(MANIFEST[p]["type"] == typ for p in chosen):
            chosen.append(default)
    kept = set()  # one piece per type: the model's first choice
    chosen = [p for p in chosen if not (MANIFEST[p]["type"] in kept or kept.add(MANIFEST[p]["type"]))]
    d["pieces"] = sorted(chosen, key=lambda p: ORDER.index(MANIFEST[p]["type"]))
    d["review"] = review
    arabic = lambda s: bool(re.search(r"[؀-ۿ]", str(s)))
    d["caps"] = [c for c in d.get("caps") or [] if arabic(c)]  # an Arabic site: no English words over the footage
    d["heroLines"] = [" ".join(str(h).split()[:5]) for h in ([h for h in d.get("heroLines") or [] if arabic(h)] or d.get("heroLines") or [])][:3]
    # the map searches words, never a link (a link shows the whole world): the address, then the name to pin it
    link = re.search(r"https?://(?:www\.)?(?:google\.[a-z.]+/maps|maps\.app\.goo\.gl|goo\.gl/maps)\S*", request)
    d["mapsLink"] = link.group(0) if link else ""
    d["maps"] = " ".join(x for x in (str(d.get("address") or "").strip(), str(d.get("name") or "")) if x and not x.startswith("http"))
    d["colors"] = palette(d.get("colors"))
    d["shape"] = d.get("shape") if d.get("shape") in ("round", "arch", "sharp", "soft", "organic") else "round"
    d["motion"] = d.get("motion") if d.get("motion") in ("calm", "lively", "cinematic") else "lively"
    d["features"] = [str(x)[:40] for x in d.get("features") or [] if str(x).strip()][:4]
    f = d.get("fonts") or {}
    d["fonts"] = {"display": f.get("display") if f.get("display") in FONTS_OK else "Alexandria",  # no Kufi display fonts (the owner's taste)
                  "text": f.get("text") if f.get("text") in FONTS_OK else "IBM Plex Sans Arabic"}
    seen = set()  # never the same item twice
    for c in d.get("menu") or []:
        c["items"] = [i for i in c.get("items") or [] if isinstance(i, dict) and i.get("name") and not (i["name"] in seen or seen.add(i["name"]))]
        for i in c["items"]:  # the page adds the currency itself: keep the number only ("50 ريال" → "50")
            num = re.search(r"\d+(?:\.\d+)?", str(i.get("price", "")).translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")))
            i["price"] = num.group() if num else ""
    d.setdefault("media", {})
    return d


# ------------------------------------------------------------------ assemble: pieces + data.js → a site folder
def assemble(data: dict, dest: Path) -> Path:
    files = list(dict.fromkeys(MANIFEST[p]["file"] for p in data["pieces"]))
    js = "\n".join((PIECES / f).read_text(encoding="utf-8") for f in files)
    page = f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{_attr(data.get('lede', ''))}">
<meta property="og:title" content="{_attr(data.get('name', ''))}">
<meta property="og:description" content="{_attr(data.get('tagline', ''))}">
<meta name="theme-color" content="{_attr((data.get('colors') or {}).get('ink', '#141210'))}">
<title>{_attr(data.get('name', ''))}</title>
<link rel="icon" href="{_attr(data.get('logo') or 'data:,')}">
<script>document.documentElement.classList.add('js')</script>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<script src="data.js"></script>
<style>
{(HERE / 'base.css').read_text(encoding='utf-8')}</style>
</head>
<body>
<div id="app"></div>
<script src="{LENIS}"></script>
<script>
{js}
</script>
<script>
{(HERE / 'runtime.js').read_text(encoding='utf-8')}</script>
</body>
</html>
"""
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "index.html").write_text(page, encoding="utf-8")
    (dest / "data.js").write_text("window.SITE = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
    (dest / ".nojekyll").write_text("", encoding="utf-8")
    return dest


def _attr(s: str) -> str:
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


# ------------------------------------------------------------------ the whole line
def load(dest: Path) -> dict:
    return json.loads((dest / "data.js").read_text(encoding="utf-8").split("=", 1)[1].strip().rstrip(";"))


def polish(dest: Path, instruction: str, ask=None, log=print) -> dict:
    """The API art director edits the site through its data only (texts, menu, colors, fonts, which pieces and their
    order): the pieces' code is never touched, so an edit can't break the page. Rebuilds and re-checks it."""
    from . import media, review
    data = load(dest)
    keep_media, keep = data.get("media", {}), {k: data[k] for k in ("whatsapp", "country", "currency", "lang", "credits", "address", "hours", "mapsLink", "order", "instagram", "tiktok") if k in data}
    nl = "\n"
    pieces = nl.join(f"- {k}: {v['type']}, style {','.join(v['style'])}, needs {','.join(v['needs']) or '-'}" for k, v in MANIFEST.items())
    shown = {k: v for k, v in data.items() if k not in ("media", "review")}
    prompt = (f"You are the art director of Weblume, a web studio. This is the content file of a client's website:{nl}"
              f"{json.dumps(shown, ensure_ascii=False)}{nl}{nl}WHAT TO CHANGE:{nl}{instruction}{nl}{nl}Rewrite the file to fix all of it. "
              "You may change texts, the menu, colors, fonts and which pieces are used and their order. Keep the same dialect and "
              "currency, keep every true fact, never invent reviews, ratings or phone numbers. Copy must sound like a premium "
              f"local brand: short, warm, specific.{nl}{nl}PIECES:{nl}{pieces}{nl}{nl}Answer with the whole JSON object only, same shape.")
    new = rules.extract_json((ask or _ask_cloud)(prompt))
    if weak(new):
        raise RuntimeError(f"The art director's edit was unusable: {weak(new)}")
    new.update(keep)
    new["media"] = keep_media
    new = normalize(new, f"{data.get('name', '')} {keep.get('whatsapp', '')} {keep.get('mapsLink', '')}", keep.get("country", ""))
    new.update({k: keep[k] for k in ("address", "hours", "order", "instagram", "tiktok") if k in keep})
    new["maps"] = " ".join(x for x in (str(new.get("address") or ""), str(new.get("name") or "")) if x)
    new["review"] = data.get("review", [])
    media.swap(new)
    assemble(new, dest)
    issues, shots = review.check(dest)
    log("   التعديل اتطبق واتراجع في المتصفح")
    return {"data": new, "issues": issues, "shots": shots}


def judge(shots: list[str], request: str) -> dict:
    """Tarek looks at the screenshots (vision model): a score and the most important problems."""
    from .. import tester
    notes = ("This site is assembled from Weblume's tested pieces: judge the design, copy, photos and colors, not the code. "
             "The hero plays footage with the scroll, so a frame may look blurred mid-motion; pinned sections are caught mid-animation (a clip still small, a row mid-slide); the Google map iframe often shows grey in automated screenshots but loads for visitors. None of these are problems.")
    return tester.judge([Path(s) for s in shots if "desktop" in s or "phone" in s][:8], request, notes)


ROUNDS = 2


def build(request: str, client_photos: Path | None = None, ask=None, log=print, polisher=None) -> dict:
    from . import media, review
    log("1/5 الموديل بيكتب محتوى الموقع…")
    data = plan(request, ask)
    dest = OUTPUT_DIR / "factory" / rules.slug(data.get("word") or data["name"], "site")
    if dest.exists():
        shutil.rmtree(dest)
    log(f"2/5 بجيب الصور والفيديو لـ «{data['name']}»…")
    media.fill(data, dest, client_photos, log)
    log("3/5 بركّب القطع…")
    assemble(data, dest)
    log("4/5 بفتح الموقع في المتصفح وبراجعه…")
    issues, shots = review.check(dest)
    if issues:  # one automatic repair round: drop what failed to load, rebuild, check again
        media.drop_broken(data, issues)
        assemble(data, dest)
        issues, shots = review.check(dest)
    verdict = None
    for rnd in range(1, ROUNDS + 1):  # the API art director: Tarek scores it, the stronger model edits until it passes
        try:
            verdict = judge(shots, request)
        except Exception as e:
            log(f"   طارق مقدرش يشوف الموقع: {e}")
            break
        log(f"   طارق: {verdict['score']:g}/10")
        if verdict["verdict"] == "PASS":
            break
        fixes = "\n".join(f"- {p.get('where', '')}: {p.get('problem', '')} -> {p.get('fix', '')}" for p in verdict.get("problems") or [])
        log(f"   المدير الفني بيعدّل (جولة {rnd})…")
        try:
            out = polish(dest, f"Tarek (QA, {verdict['score']:g}/10) found:\n{fixes}", ask=polisher, log=log)
            data, issues, shots = out["data"], out["issues"], out["shots"]
        except Exception as e:
            log(f"   التعديل مانفعش: {e}")
            break
    save_example(request, data, dest)
    zipped = shutil.make_archive(str(dest), "zip", dest)
    log("5/5 جاهز.")
    return {"name": data["name"], "folder": str(dest), "zip": zipped, "pieces": data["pieces"], "shots": shots, "test": verdict,
            "issues": issues, "review": data["review"], "preview": f"http://127.0.0.1:8501/site/factory/{dest.name}/"}
