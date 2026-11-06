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
p = company.parse_plan('{"agents":["hana","karim","boss"],"client_name":"Noir"}', "x")
assert p["agents"] == ["karim", "hana"] and p["client_name"] == "Noir"
assert company.parse_plan("no json here", "اعمل موقع لكافيه")["agents"] == ["omar", "nour", "karim", "hana"]
assert company.parse_plan("??", "write tiktok captions")["agents"] == ["sara"]
# a website request whose plan forgot the developer still gets the whole website team
p = company.parse_plan('{"agents":["omar","nour","sara"]}', "Build a website for Noir café, plus TikTok ideas")
assert p["agents"] == ["omar", "nour", "karim", "hana", "sara"], p

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
for kind in templates.KINDS:
    page = templates.load(kind)
    assert templates.CSS_MARK in page and templates.JS_MARK in page, kind
    done = templates.inject_motion(page)
    assert templates.CSS_MARK not in done and "IntersectionObserver" in done and done.count("wl-motion-kit") == 1
    assert templates.inject_motion(done) == done  # running twice changes nothing
lost = templates.inject_motion("<html><head></head><body>x</body></html>")  # Karim dropped the markers
assert lost.index("wl-motion-kit") < lost.index("</head>") and lost.index("IntersectionObserver") < lost.index("</body>")

# Stock photos become placeholders for the client's real photos; invented claims are flagged
html, n = templates.strip_stock_photos('<img class="hero ph" src="https://images.unsplash.com/photo-1?w=800" alt="بار القهوة"> <img src="logo.png" alt=""><meta property="og:image" content="https://images.pexels.com/x.jpg">')
assert n == 2 and "pexels" not in html and 'class="ph hero"' in html and "بار القهوة · صورة حقيقية من العميل" in html and 'src="logo.png"' in html, html
assert len(templates.claims_to_check('<h2>آراء زوارنا</h2><b data-count="6">0</b>')) == 2
assert templates.claims_to_check("<h1>قهوة</h1>") == []

print("All rule checks passed.")
