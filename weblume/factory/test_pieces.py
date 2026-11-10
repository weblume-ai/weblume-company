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
    "address": "الرياض، حي العليا", "maps": "Riyadh Olaya", "whatsapp": "966500000000", "country": "SA", "currency": "ر.س", "lang": "ar", "review": [],
    "media": {"frames": {"d": "assets/frames-d/", "m": "assets/frames-m/", "n": 162}, "video": "assets/clip.mp4", "poster": "assets/poster.webp",
              "heroImg": "assets/img/mood-hall.webp", "about": {"src": "assets/img/mood-chair.webp", "alt": "ركن"},
              "gallery": [{"src": f"assets/img/mood-{n}.webp", "alt": "الأجواء"} for n in ("hall", "stools", "tile", "yellow", "chair")]}}


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
    for pid in MANIFEST:
        data = dict(DEMO, pieces=[pid])
        assemble(data, dest)
        issues, shots = review.check(dest)
        issues = [i for i in issues if not i.startswith("MAP") or pid == "visit"]  # the map check is only for the visit piece
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
