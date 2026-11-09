"""Design ideas for a new site: a direction, a hero and section blueprints, and real award-winning sites in the
same business, picked from knowledge/inspiration/ (MIT tasteskill library). Ideas to adapt, never to copy."""
import hashlib
import json
import re
from functools import lru_cache

from .config import ROOT

LIB = ROOT / "knowledge" / "inspiration"
SECTORS = {  # our kinds / words -> the library's sectors
    "restaurant": ["restaurant", "hospitality"], "cafe": ["restaurant", "hospitality"],
    "clinic": ["health"], "shop": ["ecommerce", "physical-product", "fashion"],
    "game": ["consumer-app", "culture", "event", "other"], "portfolio": ["personal-portfolio", "studio-portfolio"],
    "agency": ["agency", "studio-portfolio"], "event": ["event", "culture"], "music": ["music", "culture"],
    "realestate": ["real-estate", "architecture"], "school": ["education", "culture"], "app": ["consumer-app", "saas", "ai-product"],
}
WORDS = {
    "game": ["game", "gaming", "play", "لعبة", "ألعاب", "العاب", "جيم"], "portfolio": ["portfolio", "بورتفوليو", "أعمالي", "سيرة"],
    "restaurant": ["restaurant", "مطعم", "مشويات", "بيتزا", "برجر"], "event": ["event", "wedding", "فرح", "حفلة", "مؤتمر", "ايفنت"],
    "music": ["music", "band", "موسيقى", "مزيكا"], "realestate": ["real estate", "عقارات", "شقق"], "school": ["school", "course", "كورس", "مدرسة", "أكاديمية"],
    "app": ["app", "saas", "تطبيق", "ابلكيشن"], "agency": ["agency", "studio", "وكالة", "شركة تسويق"],
}
AVOID = re.compile(r"\bgold|gradient mesh|glassmorph", re.I)  # the owner's taste: no gold, no generic gradients


@lru_cache
def _load(name: str) -> list:
    return json.loads((LIB / f"{name}.json").read_text(encoding="utf-8"))


def sector(text: str, kind: str = "") -> str:
    t = text.lower()
    hit = max(WORDS, key=lambda k: sum(w in t for w in WORDS[k]))
    return hit if any(w in t for w in WORDS[hit]) else (kind if kind in SECTORS else "agency")


def _cut(s, n):
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


def brief(text: str, kind: str = "", sites: int = 3) -> str:
    """A design direction and references for this request. The same request gets the same pick; a new one differs."""
    sec = SECTORS[sector(text, kind)]
    seed = int(hashlib.sha1(text.encode()).hexdigest(), 16)
    dirs = [d for d in _load("directions") if set(d["sectors"]) & set(sec) and not AVOID.search(json.dumps(d))] \
        or [d for d in _load("directions") if not AVOID.search(json.dumps(d))]
    d = dirs[seed % len(dirs)]
    heroes = [h for h in _load("heroes") if d["id"] in h["directions"]] or _load("heroes")
    hero = heroes[seed % len(heroes)]
    secs, roles = [], set()
    for s in sorted((s for s in _load("sections") if d["id"] in s["directions"]), key=lambda s: (seed + len(s["id"])) % 97):
        if s["role"] not in roles and s["role"] not in ("testimonial", "stats", "proof", "pricing"):  # no invented numbers or reviews
            roles.add(s["role"])
            secs.append(s)
        if len(secs) == 4:
            break
    refs = [s for s in _load("sites") if s["kind"] in sec] or _load("sites")
    refs = [refs[(seed + i * 7) % len(refs)] for i in range(min(sites, len(refs)))]
    out = [f"DESIGN DIRECTION «{d['name']}»: {_cut(d['idea'], 420)}",
           f"Composition: {_cut(d.get('composition'), 300)}", f"Type: {_cut(d.get('typography'), 220)}",
           f"Colour: {_cut(d.get('colour'), 200)} (use the client's own brand colors inside this idea)",
           f"Motion: {_cut(d.get('motion'), 160)}", f"Avoid: {_cut(d.get('pitfalls'), 200)}",
           f"HERO «{hero['name']}»: {_cut(hero['blueprint'], 520)}"]
    out += [f"SECTION ({s['role']}) «{s['name']}»: {_cut(s['blueprint'], 300)}" for s in secs]
    out += ["REAL SITES TO LEARN FROM (ideas only, never copy): " + " | ".join(
        f"{r['name']} ({r['url']}): {_cut(r['idea'], 140)} Take: {_cut(r.get('steal'), 120)}" for r in refs)]
    return "\n".join(out)
