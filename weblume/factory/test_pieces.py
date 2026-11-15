"""Test every piece alone at 360, 768 and 1280 px with real media (Loopie's), and make its thumbnail for the manifest.
    python -m weblume.factory.test_pieces"""
import json
import shutil
from pathlib import Path

from . import MANIFEST, PIECES, assemble, review
from ..config import OUTPUT_DIR

CAFE = Path(__file__).resolve().parents[1] / "templates" / "cafe" / "assets"
DEMO = {
    "name": "قهوة تجربة", "word": "تجربة", "heroLines": ["نختلف عالجو..", "ونتفق عالقهوة"], "tagline": "قهوة مختصة وحلا",
    "lede": "قهوة مختصة وحلا في قلب المدينة.", "about": "مكان هادي للشغل والقعدة الحلوة، بن مختار بعناية وحلا بيتعمل كل يوم.",
    "together": "القهوة تجمعنا.", "invite": "تعالى اقعد عندنا", "caps": ["حصاد.", "طحن.", "استخلاص."],
    "colors": {"ink": "#141210", "paper": "#ffffff", "accent": "#EBB81F", "muted": "#B9B1A7", "surface": "#221f1b", "onAccent": "#141210"},
    "fonts": {"display": "Alexandria", "text": "IBM Plex Sans Arabic"},
    "menu": [{"cat": "القهوة", "img": "assets/img/menu-coffee.webp", "items": [
        {"name": "إسبريسو", "desc": "بن إثيوبي · مختص", "price": "14", "img": "assets/img/drink-esp.webp"},
        {"name": "كابتشينو", "desc": "حليب · رغوة", "price": "18", "img": "assets/img/drink-capp.webp"},
        {"name": "أمريكانو", "desc": "إسبريسو · ماء", "price": "15", "img": "assets/img/drink-amer.webp"}]},
        {"cat": "الحلا", "img": "assets/img/menu-dessert.webp", "items": [
            {"name": "تشيز كيك", "desc": "توت", "price": "22", "img": "assets/img/mood-cup.webp"},
            {"name": "ماتشا", "desc": "ماتشا · حليب", "price": "20", "img": "assets/img/drink-green.webp"}]}],
    "features": ["قهوة مختصة من 12 بلد", "مفتوحين 18 ساعة", "جلسات عائلية"], "shape": "arch",
    # products for hero-showcase (the menu photos stand in for cut-outs), so that piece is really tested
    "showcase": [{"name": n, "desc": d, "price": pr, "cut": f"assets/img/{img}.webp", "tone": tn, "ink": "#ffffff"} for n, d, pr, img, tn in
                 (("إسبريسو", "بن إثيوبي", "14", "drink-esp", "#c2410c"), ("كابتشينو", "حليب · رغوة", "18", "drink-capp", "#7c3aed"),
                  ("ماتشا", "ماتشا · حليب", "20", "drink-green", "#15803d"))],
    "address": "الرياض، حي العليا", "maps": "Riyadh Olaya", "whatsapp": "966500000000", "country": "SA", "currency": "ر.س", "lang": "ar", "review": [],
    "media": {"frames": {"d": "assets/frames-d/", "m": "assets/frames-m/", "n": 162}, "video": "assets/clip.mp4", "poster": "assets/poster.webp",
              "heroImg": "assets/img/mood-hall.webp", "about": {"src": "assets/img/mood-chair.webp", "alt": "ركن"},
              "gallery": [{"src": f"assets/img/mood-{n}.webp", "alt": "الأجواء"} for n in ("hall", "stools", "tile", "yellow", "chair")]}}


def _profiles(base: Path) -> list[tuple[dict, Path]]:
    """Each piece is tested and pictured on a different shop, so the pieces don't all look like Loopie: the café
    demo plus real factory sites on this laptop (flowers, grills, sweets) when they exist."""
    from . import FEELS, load
    out = []
    for i, name in enumerate(("فل", "السفرة", "نوتيلا")):
        site = OUTPUT_DIR / "factory" / name
        if not (site / "data.js").is_file():
            continue
        d, dest = load(site), base.with_name(f"{base.name}-{i + 1}")
        if not (dest / "assets").exists():
            shutil.copytree(site / "assets", dest / "assets")
        items = [it for c in d.get("menu") or [] for it in c.get("items") or [] if it.get("img")]
        d["showcase"] = [{"name": it["name"], "desc": it.get("desc", ""), "price": it.get("price", ""), "cut": it["img"], "tone": t, "ink": "#ffffff"}
                         for it, t in zip(items[:3], ("#c2410c", "#7c3aed", "#15803d"))]
        nums = [f for f in d.get("features") or [] if any(ch.isdigit() for ch in f)]
        d["features"] = (d.get("features") or [])[:2] + ["مفتوحين 16 ساعة", "أكتر من 20 صنف"][:max(0, 2 - len(nums))]
        d.update(feel=FEELS[i % len(FEELS)], picked=[], review=[])
        out.append((d, dest))
    return out


def main():
    dest = OUTPUT_DIR / "factory" / "_pieces-test"
    if not (dest / "assets" / "frames-d").exists():
        shutil.rmtree(dest, ignore_errors=True)
        shutil.copytree(CAFE / "brew-d", dest / "assets" / "frames-d")
        shutil.copytree(CAFE / "brew-m", dest / "assets" / "frames-m")
        shutil.copytree(CAFE / "img", dest / "assets" / "img")
        shutil.copy(CAFE / "pour.mp4", dest / "assets" / "clip.mp4")
        shutil.copy(CAFE / "pour.webp", dest / "assets" / "poster.webp")
    thumbs, bad = PIECES / "thumbs", {}
    thumbs.mkdir(exist_ok=True)
    shops = [(DEMO, dest)] + _profiles(dest)
    from PIL import Image, ImageStat
    blank = lambda shot: ImageStat.Stat(Image.open(shot).convert("L").crop((0, 80, 1280, 800))).stddev[0] < 12
    for k, pid in enumerate(MANIFEST):
        for t in range(len(shops)):  # a piece that shows nothing on this shop (missing data) is tried on the next one
            shop, where = shops[(k + t) % len(shops)]
            assemble(dict(shop, pieces=[pid]), where)
            issues, shots = review.check(where)
            desk = next((s for s in shots if "desktop_0" in s), None)
            if pid in ("nav", "bar", "marquee-band") or not desk or not blank(desk):
                break
        if issues:
            bad[pid] = issues
        desk = next((s for s in shots if "desktop_0" in s), None)
        if desk:
            from PIL import Image
            with Image.open(desk) as im:
                im.convert("RGB").resize((480, 300)).save(thumbs / f"{pid}.webp", "WEBP", quality=70)
        print(pid, "OK" if not issues else issues, flush=True)
    m = json.loads((PIECES / "manifest.json").read_text(encoding="utf-8"))
    for pid in m:
        m[pid]["thumb"] = f"thumbs/{pid}.webp"
        m[pid]["tested"] = "360/768/1280 OK" if pid not in bad else "; ".join(bad[pid])[:300]
    (PIECES / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    return bad


if __name__ == "__main__":
    print("problems:", main())
