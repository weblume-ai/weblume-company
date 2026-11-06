"""Checks for the business rules. Run:  python tests\\test_rules.py"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from weblume import company, config, rules  # noqa: E402

# Sara: phone numbers never survive
for text in ["كلمنا على 01012345678", "Call +20 101 234 5678 now", "واتساب: ٠١٠١٢٣٤٥٦٧٨", "wa.me/201012345678",
             "https://api.whatsapp.com/send?phone=2010"]:
    out, n = rules.remove_phone_numbers(text)
    assert n >= 1 and not any(ch.isdigit() for ch in out.replace(config.WEBSITE, "")), (text, out)
for text in ["Since 2019, open 9:00-23:00", "السعر 1500 جنيه"]:
    assert rules.remove_phone_numbers(text) == (text, 0), text

# Ziad: already-contacted businesses are caught even with small spelling differences
with tempfile.TemporaryDirectory() as d:
    rules.CONTACTED_FILE = Path(d) / "contacted.json"
    assert rules.load_contacted() == []
    assert rules.mark_contacted("Bean There Café", "Mansoura") is True
    assert rules.mark_contacted("bean there cafe") is False  # same business, no accent
    assert rules.is_contacted("مَطعم  Hend", [{"business": "مطعم hend"}])
    assert rules.mark_contacted("كافيه الأمورة") is True
    contacted = rules.load_contacted()
    new, old = rules.split_contacted(["BEAN THERE café", "Koshary Hend", "كافيه الامورة", "Koshary Hend", " "], contacted)
    assert new == ["Koshary Hend"] and old == ["BEAN THERE café", "كافيه الامورة"], (new, old)
    rules.CONTACTED_FILE.write_text("{broken", encoding="utf-8")
    try:
        rules.load_contacted()
        raise AssertionError("broken contacted.json must not count as empty")
    except RuntimeError:
        pass

# Model answers
assert rules.extract_json('Sure!\n```json\n{"agents":["karim"]}\n```') == {"agents": ["karim"]}
# the real Gemini answer that broke: plain quotes inside an Arabic message
bad = '{\n  "leads": [\n    {\n      "business": "Koshary Hend",\n      "message": "يا جماعة، "كشري هند" سمعته حلوة"\n    }\n  ]\n}'
assert rules.extract_json(bad)["leads"][0]["message"] == 'يا جماعة، "كشري هند" سمعته حلوة'
assert rules.extract_html("Here:\n```html\n<!DOCTYPE html><html><body>x</body></html>\n```\nDone") == \
    "<!DOCTYPE html><html><body>x</body></html>"
assert rules.slug("Bean There Café!") == "bean-there-café" and rules.slug("كافيه نور") == "كافيه-نور"
assert rules.slug("***") == "client"

# Layla's plan: valid JSON is used, garbage falls back to keywords, unknown agents are dropped
p = company.parse_plan('{"agents":["mostafa","karim","boss"],"client_name":"Noir"}', "x")
assert p["agents"] == ["karim", "mostafa"] and p["client_name"] == "Noir"
assert company.parse_plan("no json here", "اعمل موقع لكافيه")["agents"] == ["omar", "youssef", "karim", "mostafa", "tarek"]
assert company.parse_plan("??", "write tiktok captions")["agents"] == ["adam"]
# a website request whose plan forgot the developer still gets the whole website team
p = company.parse_plan('{"agents":["omar","youssef","adam"]}', "Build a website for Noir café, plus TikTok ideas")
assert p["agents"] == ["omar", "youssef", "karim", "mostafa", "tarek", "adam"], p

# Busy model (503 / quota) hands the same call to the next model; other errors still stop the run
from crewai import LLM  # noqa: E402
a, b = LLM(model="ollama/a", api_key="x"), LLM(model="ollama/b", api_key="x")
def busy(*_, **__): raise RuntimeError("503 UNAVAILABLE high demand")
def broken(*_, **__): raise ValueError("bad request")
object.__setattr__(a, "call", busy); object.__setattr__(b, "call", lambda *_, **__: "from b")
assert config.with_fallback([a, b]).call("hi") == "from b"
c = LLM(model="ollama/c", api_key="x"); object.__setattr__(c, "call", broken)
try:
    config.with_fallback([c, b]).call("hi")
    raise AssertionError("a real error must not be hidden by the fallback")
except ValueError:
    pass

# Templates: the right one is picked, and the motion kit always ends up in the page exactly once
from weblume import templates  # noqa: E402
assert templates.pick("موقع لكافيه نوار") == "cafe" and templates.pick("Build a site for a dental clinic") == "clinic"
assert templates.pick("متجر عطور أونلاين") == "shop" and templates.pick("something else") == "cafe"
for kind in set(templates.KINDS) - templates.FOLDER:
    page = templates.load(kind)
    assert templates.CSS_MARK in page and templates.JS_MARK in page, kind
    done = templates.inject_motion(page)
    assert templates.CSS_MARK not in done and "IntersectionObserver" in done and done.count("wl-motion-kit") == 1
    assert templates.inject_motion(done) == done  # running twice changes nothing
lost = templates.inject_motion("<html><head></head><body>x</body></html>")  # Karim dropped the markers
assert lost.index("wl-motion-kit") < lost.index("</head>") and lost.index("IntersectionObserver") < lost.index("</body>")

# Photo links that don't load become placeholders for real photos; working stock photos stay; claims are flagged
page = '<img class="hero" src="https://dead.example/1.jpg" alt="بار القهوة"> <img src="https://ok.example/2.jpg" alt=""> <img src="logo.png" alt="">'
html, n = templates.fix_broken_images(page, check=lambda url: "ok." in url)
assert n == 1 and 'class="ph hero"' in html and "بار القهوة · صورة حقيقية من العميل" in html, html
assert "https://ok.example/2.jpg" in html and 'src="logo.png"' in html

# Café template (the Loopie design): Karim's JSON becomes a whole site; made-up image paths are repaired
import tempfile, json as _json  # noqa: E401,E402
with tempfile.TemporaryDirectory() as d:
    data = {"name": "Noir", "word": "نوار", "drinks": [{"name": "لاتيه", "img": "assets/img/drink-capp.webp"},
            {"name": "x", "img": "assets/img/made-up.webp"}], "aboutPhoto": {"src": "photos/fake.jpg", "alt": ""}}
    fixed = templates.build_site("cafe", data, Path(d) / "noir")
    site = Path(d) / "noir"
    assert fixed == 2 and (site / "index.html").is_file() and (site / "assets/brew-d").is_dir()
    assert not (site / "example-data.js").exists() and not (site / "GUIDE.md").exists()
    js = (site / "data.js").read_text(encoding="utf-8")
    back = _json.loads(js[len("window.CAFE = "):].rstrip().rstrip(";"))
    assert back["demo"] is True and back["drinks"][1]["img"] == "assets/img/menu-coffee.webp" and back["aboutPhoto"]["src"] == "assets/img/mood-cup.webp"
assert "window.CAFE" in templates.load("cafe") and "drink-esp.webp" in templates.guide("cafe")
assert len(templates.claims_to_check('<h2>آراء زوارنا</h2><b data-count="6">0</b>')) == 2
assert templates.claims_to_check("<h1>قهوة</h1>") == []

# Prices and hours that the owner never gave are removed; the ones he gave stay
menu = {"menu": [{"name": "قهوة", "items": [{"name": "اسبريسو", "price": 35}, {"name": "لاتيه", "price": 60}, {"name": "x", "price": ""}]}],
        "hours": {"0": {"open": "08:00", "close": "00:00"}}}
gone = templates.drop_unsourced(menu, "كافيه نوار، اللاتيه بـ ٦٠ جنيه")
assert menu["menu"][0]["items"][0]["price"] == "" and menu["menu"][0]["items"][1]["price"] == 60 and "hours" not in menu, menu
assert gone == ["price", "hours"]
kept = {"hours": "24h"}
assert templates.drop_unsourced(kept, "مفتوح 24 ساعة") == [] and kept["hours"] == "24h"

with tempfile.TemporaryDirectory() as d:  # no drinks at all must not break the page
    empty = {"name": "x", "drinks": []}
    templates.build_site("cafe", empty, Path(d) / "x")
    assert len(empty["drinks"]) == 1 and "shot=" not in (Path(d) / "x" / "index.html").read_text(encoding="utf-8")

print("All rule checks passed.")
