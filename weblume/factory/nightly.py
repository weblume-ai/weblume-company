"""Nightly practice: the factory builds N varied sites for imaginary places, so the local model's training examples
grow every day (the API art director corrects each one; the owner approves the good ones).

    python -m weblume.factory.nightly            (10 sites)
    python -m weblume.factory.nightly 3          (3 sites)

Every place is imaginary (no real business, phone or address). A picture of each site is kept
(knowledge/factory-examples/nightly/shots/) so the owner can look before approving:
    python -m weblume.factory approve <name>
Unapproved practice sites older than 14 days are deleted from output/factory to save disk space."""
import json
import random
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

from . import EXAMPLES, build
from ..config import OUTPUT_DIR

NIGHT = EXAMPLES / "nightly"  # a folder of its own: the examples folder holds only examples
DONE = NIGHT / "done.json"  # every request already built, so no place is made twice
SHOTS = NIGHT / "shots"

# kind, Arabic description, words for imaginary names, what such a place says about itself
KINDS = [
    ("cafe", "كافيه قهوة مختصة", ["حبة", "رشفة", "بُنّ", "فنجان", "صباح", "مزاج", "ركن", "قهوتنا"], ["قهوة مختصة", "حلويات بيتي", "جلسات هادية للشغل"]),
    ("restaurant", "مطعم مشويات", ["الفحم", "الجمر", "شواية", "النار", "المشوى", "أبو جبل"], ["مشويات على الفحم", "توصيل", "جلسات عائلية"]),
    ("restaurant", "مطعم أكل بيتي", ["سفرة", "طبخة", "لمة", "بيتنا", "صينية", "ستي"], ["أكل بيتي كل يوم", "طواجن", "وجبات للمكاتب"]),
    ("sweets", "محل حلويات شرقية", ["قطايف", "شربات", "حلاوة", "كنافتنا", "بسبوستي", "السكرية"], ["كنافة طازة", "حلويات رمضان", "طلبات للمناسبات"]),
    ("sweets", "محل آيس كريم وجيلاتو", ["تلجة", "بوظة", "جيلاتو", "برد", "مثلّج", "قمع"], ["نكهات فواكه طبيعية", "جيلاتو إيطالي", "مكان للعيلة"]),
    ("bakery", "مخبز ومعجنات", ["رغيف", "عجينة", "الفرن", "خميرة", "مخبزنا", "طابون"], ["عيش طازة كل صبح", "معجنات وفطائر", "كرواسون"]),
    ("cafe", "كافيه وعصاير فريش", ["عصارة", "فريش", "ليمونة", "مانجة", "كوكتيل", "نعناع"], ["عصاير طبيعية", "سموزي", "مفتوح لآخر الليل"]),
    ("restaurant", "مطعم برجر", ["برجرنا", "الصاج", "بن", "ساندوتش", "ستريت", "جريل"], ["برجر لحم بلدي", "بطاطس مقرمشة", "توصيل سريع"]),
    ("restaurant", "مطعم مأكولات بحرية", ["الصياد", "البحر", "المينا", "سمكة", "الموج", "شبكة"], ["سمك طازة كل يوم", "صواني جمبري", "شوي وقلي"]),
    ("restaurant", "مطعم بيتزا ومعجنات", ["فرن الحطب", "بيتزتنا", "عجين", "نابولي", "الطاحونة", "بيتزاريا"], ["فرن حطب", "عجينة متخمرة", "توصيل"]),
    ("shop", "محل ورد وهدايا", ["وردة", "بوكيه", "ياسمين", "زهرة", "هدية", "فل"], ["بوكيهات حسب الطلب", "توصيل نفس اليوم", "تغليف هدايا"]),
    ("shop", "محل عطور", ["عود", "مسك", "عنبر", "بخور", "عطرنا", "زيت"], ["عطور شرقية", "خلطات خاصة", "تغليف هدايا"]),
    ("clinic", "عيادة أسنان", ["ابتسامة", "سنة", "لؤلؤة", "بسمة", "ناب", "ضرس"], ["تنظيف وتبييض", "تقويم", "مواعيد مسائية"]),
    ("gym", "جيم ولياقة", ["قوة", "نبض", "عضلة", "حديد", "تمرين", "طاقة"], ["أجهزة حديثة", "مدربين", "قسم للسيدات"]),
    ("salon", "صالون حلاقة رجالي", ["مقص", "شنب", "موس", "دقن", "ستايل", "كوافير"], ["حلاقة وتهذيب دقن", "حجز بالميعاد", "عناية بالبشرة"]),
]
EG = ["القاهرة", "الإسكندرية", "المنصورة", "طنطا", "الجيزة", "أسيوط", "الزقازيق", "بورسعيد"]
SA = ["الرياض", "جدة", "الدمام", "الخبر", "مكة", "المدينة", "أبها", "الطائف"]
PRICES = {"cafe": [("لاتيه", 45, 18), ("كابتشينو", 40, 16), ("موهيتو", 50, 20)], "restaurant": [("وجبة اليوم", 120, 45), ("طبق مشكل", 220, 80)],
          "sweets": [("كيلو كنافة", 180, 60), ("كوباية آيس كريم", 45, 18)], "bakery": [("كرواسون", 25, 9), ("فطيرة", 60, 22)]}


def requests(n: int, seed: int) -> list[str]:
    """n new requests for imaginary places, varied in kind, country, facts given and wording."""
    done = set(json.loads(DONE.read_text(encoding="utf-8"))) if DONE.exists() else set()
    rnd, out, tries = random.Random(seed), [], 0
    while len(out) < n and tries < 500:
        tries += 1
        kind, what, names, strengths = rnd.choice(KINDS)
        saudi = rnd.random() < .45
        city = rnd.choice(SA if saudi else EG)
        name = rnd.choice(names) + rnd.choice(["", "", " هاوس", " ستوديو", " بوتيك", " كورنر"]) if kind in ("cafe", "sweets", "shop") else rnd.choice(names)
        parts = [f"اعمل موقع ل{what} {'اسمها' if what.startswith('عيادة') else 'اسمه'} {name} في {city}"]
        if rnd.random() < .6:
            parts.append("عندنا " + " و".join(rnd.sample(strengths, k=rnd.randint(1, len(strengths)))))
        if kind in PRICES and rnd.random() < .5:  # some requests give real prices, so the model learns to keep facts exactly
            item, eg, sa = rnd.choice([p for p in PRICES[kind] if ("آيس" in p[0]) == ("آيس" in what)] or PRICES[kind])
            parts.append(f"{item} بـ{sa if saudi else eg} {'ريال' if saudi else 'جنيه'}")
        if rnd.random() < .3:
            parts.append(rnd.choice(["مفتوحين من 8 الصبح لـ12 بالليل", "مفتوحين 24 ساعة", "مقفولين يوم الجمعة الصبح"]))
        req = "، ".join(parts)
        if req not in done and req not in out:
            out.append(req)
    return out


def _cleanup(days: int = 14):
    """Practice sites take disk space: drop unapproved ones after two weeks (their example and picture stay)."""
    approved = {f.stem for f in EXAMPLES.glob("*.json") if json.loads(f.read_text(encoding="utf-8")).get("approved")} if EXAMPLES.exists() else set()
    for site in (OUTPUT_DIR / "factory").glob("*"):
        if site.is_dir() and site.name not in approved and not site.name.startswith("_") and time.time() - site.stat().st_mtime > days * 86400 \
                and (EXAMPLES / f"{site.name}.json").exists() and "nightly" in (EXAMPLES / f"{site.name}.json").read_text(encoding="utf-8"):
            shutil.rmtree(site, ignore_errors=True)
            Path(str(site) + ".zip").unlink(missing_ok=True)


def run(n: int = 10, log=print) -> list[dict]:
    SHOTS.mkdir(parents=True, exist_ok=True)
    reqs, results = requests(n, int(time.time())), []
    log(f"{datetime.now():%Y-%m-%d %H:%M} nightly: {len(reqs)} sites")
    for i, req in enumerate(reqs, 1):
        log(f"[{i}/{len(reqs)}] {req}")
        try:
            res = build(req, log=lambda m: log("   " + m.strip()), fresh_name=True)
            name = Path(res["folder"]).name
            ex = EXAMPLES / f"{name}.json"
            if ex.exists():  # mark it as practice, so the owner knows where it came from
                data = json.loads(ex.read_text(encoding="utf-8"))
                data["source"] = "nightly"
                ex.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            desk = next((s for s in res["shots"] if "desktop_0" in s), None)
            if desk:
                shutil.copy(desk, SHOTS / f"{name}.png")
            results.append({"request": req, "name": name, "score": (res.get("test") or {}).get("score")})
            log(f"   ✓ {name}: Tarek {results[-1]['score']}")
        except Exception as e:  # one bad site never stops the night
            results.append({"request": req, "error": str(e)[:200]})
            log(f"   ✗ {e}")
        done = json.loads(DONE.read_text(encoding="utf-8")) if DONE.exists() else []
        DONE.write_text(json.dumps(done + [req], ensure_ascii=False, indent=0), encoding="utf-8")
    _cleanup()
    return results


if __name__ == "__main__":
    out = run(int(sys.argv[1]) if len(sys.argv) > 1 else 10)
    ok = [r for r in out if "name" in r]
    print(f"done: {len(ok)}/{len(out)} sites. Look at knowledge/factory-examples/nightly/shots, then: python -m weblume.factory approve <name>")
