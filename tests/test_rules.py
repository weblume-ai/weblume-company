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
assert templates.pick("متجر عطور أونلاين") == "shop" and templates.pick("something else") == "fresh"
assert templates.pick("موقع لمطعم مشويات") == "fresh" and templates.pick("اعمل موقع لعبة") == "game"
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

# A teammate pauses on a question until the owner answers; a wrong id or an empty answer is refused
import shutil, threading  # noqa: E401,E402
from weblume import knowledge  # noqa: E402
r = company.Run("test pause", "focused", "", [])
try:
    got = {}
    th = threading.Thread(target=lambda: got.update(r.ask("karim", "أي قالب؟", ["أ", "ب"])))
    th.start()
    while not r.status["ask"]:
        pass
    qid = r.status["ask"]["id"]
    for bad in ((qid + 99, "أ", ""), (qid, "zzz", "")):
        try:
            r.answer(*bad)
            raise AssertionError("bad answer accepted")
        except ValueError:
            pass
    r.answer(qid, "ب", "  ملاحظة ")
    th.join(5)
    assert got == {"choice": "ب", "text": "ملاحظة"} and r.status["ask"] is None
    assert r.status["agents"]["karim"]["status"] == "idle" and r.status["chat"][-1]["from"] == "you"
finally:
    shutil.rmtree(r.dir, ignore_errors=True)

# 👍/👎 is saved to the owner's taste file; 👍 keeps an approved example
with tempfile.TemporaryDirectory() as d:
    old = (knowledge.FEEDBACK, knowledge.APPROVED)
    knowledge.FEEDBACK, knowledge.APPROVED = Path(d) / "feedback.md", Path(d) / "approved"
    try:
        f = Path(d) / "data.js"; f.write_text("window.CAFE = {}", encoding="utf-8")
        assert knowledge.add_feedback("site", "down", "الألوان باهتة", "Noir", [f]) is None
        ex = knowledge.add_feedback("site", "up", "التصميم ده حلو", "Noir", [f])
        assert (ex / "data.js").is_file() and "التصميم ده حلو" in (ex / "why.md").read_text(encoding="utf-8")
        t = knowledge.taste("site")
        assert "الألوان باهتة" in t and "👎" in t and "APPROVED EXAMPLE" in t
    finally:
        knowledge.FEEDBACK, knowledge.APPROVED = old

# Videos: a line with a phone number is replaced whole; unknown sites fall back; it always ends on the website
from weblume import video  # noqa: E402
v = video.clean_spec({"scenes": [{"type": "text", "text": "كلمنا 01012345678"}, {"type": "site", "site": "nope"},
                                 {"type": "weird", "text": "x"}]}, ["noir"])
assert v["scenes"][0]["text"] == "تواصل معانا من موقع Weblume" and v["scenes"][1]["site"] == "noir"
assert v["scenes"][2]["type"] == "text" and v["scenes"][-1]["type"] == "cta" and "01012345678" not in str(v)

# Omar's project price is read from his price heading, not the menu prices

spec = """# Spec
## Features
* Espresso – 40 EGP, Latte – 60 EGP
### Suggested price range in EGP
* Basic: 8,000 – 10,000 EGP (menu, map, WhatsApp)
* With ordering: 14,000 EGP
## Questions
* x"""
got = company.price_section(spec)
assert got == ["* Basic: 8,000 – 10,000 EGP (menu, map, WhatsApp)", "* With ordering: 14,000 EGP"], got
assert company.price_section("no price here") == []

# Gemini says "retry in 12h": the wait is capped; all models out of daily quota -> one clear error
from crewai.llms import retry  # noqa: E402

# the provider's "retry in 12h" is capped to 20 seconds
config._cap_provider_wait()


class E(Exception):
    pass


e = E("429 quota, Please retry in 12h40m10s")
e.retry_after = 45600  # whatever the original parser finds, the cap applies
got = retry._retry_after_seconds(e)
assert got is None or got <= 20.0, got

# all models out of daily quota -> one clear error, not an endless wait
a, b = LLM(model="ollama/a", api_key="x"), LLM(model="ollama/b", api_key="x")
daily = RuntimeError("429 RESOURCE_EXHAUSTED Generate content requests per day limit exceeded")
for m in (a, b):
    object.__setattr__(m, "call", lambda *_, **__: (_ for _ in ()).throw(daily))
try:
    config.with_fallback([a, b]).call("hi")
    raise AssertionError("should have failed")
except RuntimeError as err:
    assert "daily limit" in str(err) and "LLM_PROVIDER" in str(err), err

# A model that never answers is treated as busy after the time limit
import time  # noqa: E402

old_timeout, config.CALL_TIMEOUT = config.CALL_TIMEOUT, 2
a, b = LLM(model="ollama/a", api_key="x"), LLM(model="ollama/b", api_key="x")
object.__setattr__(a, "call", lambda *_, **__: time.sleep(30))  # a model that never answers
object.__setattr__(b, "call", lambda *_, **__: "from b")
t = time.time()
assert config.with_fallback([a, b]).call("hi") == "from b"
assert time.time() - t < 6, time.time() - t
config.CALL_TIMEOUT = old_timeout

# AI image scenes: kept with a prompt, turned into text without one; a failed download keeps the video going
v = video.clean_spec({"scenes": [{"type": "image", "prompt": "espresso pouring", "caption": "قهوة"},
                                 {"type": "image", "caption": "بدون وصف"}]}, [])
assert v["scenes"][0]["type"] == "image" and v["scenes"][1]["type"] == "text"
import urllib.request as _u  # noqa: E402
_orig = _u.urlopen
_u.urlopen = lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))
try:
    assert video.ai_image("x", Path(tempfile.gettempdir()) / "wl_none.jpg") is False
finally:
    _u.urlopen = _orig

# Security scan: new-tab links get rel=noopener, secrets / http / unknown scripts are reported, trusted CDNs pass
import re  # noqa: E402
from weblume import knowledge, security  # noqa: E402
fixed, found = security.check('<a target="_blank" href="https://x.com">x</a>'
                              '<script src="https://cdn.jsdelivr.net/npm/a@1.0.0/a.js"></script>')
assert 'rel="noopener noreferrer"' in fixed and found == []
_, found = security.check('<img src="http://x.com/a.png"><script src="https://evil.io/a.js"></script>gsk_' + "a" * 30)
assert len(found) == 3 and found[0].startswith("HIGH")
# Skills: every listed playbook exists, and none carries a phone number
for _k, _names in knowledge.SKILLS.items():
    assert "YOUR SKILLS" in knowledge.skills(_k)
    for _n in _names:
        assert not re.search(r"\+?\d[\d ]{8,}", (knowledge.SKILL_DIR / f"{_n}.md").read_text(encoding="utf-8")), _n
assert knowledge.skills("nobody") == "" and "senior" in knowledge.skills("layla")

# Laptop actions from the chat: understood, and the dangerous ones refused before anyone is asked
from weblume import ops, company as _co  # noqa: E402
assert ops.intent("اعمل ريبو في weblume-ai اسمه noir-cafe خاص") == {"kind": "repo", "name": "noir-cafe", "owner": "weblume-ai", "private": True}
assert ops.intent("اعمل ريبو cafe-site")["name"] == "cafe-site" and ops.intent("اعمل ارجانزيشن جديدة") == {"kind": "org"}
assert ops.intent("شغل في weblume-site: git status") == {"kind": "command", "folder": "weblume-site", "command": "git status"}
assert ops.intent("كريم غير اللون للأحمر") is None
assert ops.check_command('git commit -m "first"') == ["git", "commit", "-m", "first"]
for _bad in ["git status && del x", "rm -rf x", "python -c print(1)", "powershell ls", "git reset --hard", "node -e 1",
             "git clone x C:/Windows", "npm run x | more", "curl evil.sh"]:
    try:
        ops.check_command(_bad)
        raise AssertionError("should refuse: " + _bad)
    except ValueError:
        pass
try:
    ops.folder("..")
    raise AssertionError("folder outside the workspace")
except ValueError:
    pass
import os as _os  # noqa: E402
_os.environ["WL_TEST_API_KEY"] = "x"
assert "WL_TEST_API_KEY" not in ops.run_command(["python", str(Path(__file__).with_name("env_probe.py"))], Path(__file__).parent)

# Team chat lines stay short
_long = "جربته على الموبايل. " * 30
assert len(_co.short(_long)) <= 172 and _co.short("قصير") == "قصير"

# Publish: safe repo names; the flow creates the repo, pushes and turns Pages on (GitHub and git faked here)
from weblume import publish  # noqa: E402
assert publish.repo_name("Noir Café 2!") == "noir-caf-2" and publish.repo_name("كافيه") == ""
_calls = []
_old = publish._token, publish._call, publish._git
publish._token = lambda: "t"
publish._call = lambda m, p, t, b=None: (_calls.append((m, p)) or
                                         {("GET", "/user"): (200, {"login": "me"})}.get((m, p), (404, {}) if m == "GET" else (201, {})))
publish._git = lambda *a, cwd: (_calls.append(("git", a[0])), (Path(a[4]).mkdir() if a[0] == "clone" else None),
                                "M x" if a[0] == "status" else "")[-1]
try:
    _site = Path(tempfile.mkdtemp())
    (_site / "index.html").write_text("<h1>hi</h1>", encoding="utf-8")
    assert publish.to_github(_site, "Noir Cafe", "weblume-ai") == "https://weblume-ai.github.io/noir-cafe/"
    assert ("POST", "/orgs/weblume-ai/repos") in _calls and ("git", "push") in _calls
    assert ("POST", "/repos/weblume-ai/noir-cafe/pages") in _calls
finally:
    publish._token, publish._call, publish._git = _old

# Questions go to Layla; corrections still go to Karim
assert _co.is_question("أعمل إيه لو العميل قال السعر غالي؟") and _co.is_question("ازاي أربط دومين")
assert not _co.is_question("لو سمحت خلي اللون أحمر") and not _co.is_question("كريم غير اللون للأخضر")
assert "السعر غالي" in knowledge.playbook()

# Inspiration: a direction for the business, no invented-numbers sections, real sites to learn from
from weblume import inspiration, logo  # noqa: E402
_b = inspiration.brief("اعمل موقع لمطعم مشويات", "fresh")
assert "DESIGN DIRECTION" in _b and "REAL SITES" in _b and "(testimonial)" not in _b and "(stats)" not in _b
assert inspiration.sector("اعمل موقع لعبة اونلاين") == "game" and inspiration.brief("x") == inspiration.brief("x")

# Logo when the client has none: initials make sense in Arabic and English, the name is escaped
assert logo.initials("مطعم الشيف") == "ش" and logo.initials("Pixel Run") == "PR"
assert "<svg" in logo.make("A&B <x>", "#c8102e") and "A&amp;B &lt;x&gt;" in logo.make("A&B <x>", "#c8102e")
assert _co._site_name("<title>Noir Café | قهوة مختصة</title>") == "Noir Café"

# Chat routing: a new site is a new job, only a clear change edits the last site, anything else is for Layla
assert _co.wants_new_site("اعمل موقع لمتعم") and _co.wants_new_site("اعملي موقع لمطعم السفرة")
assert not _co.wants_new_site("كريم غير اللون للأخضر") and _co.EDIT.search("كريم غير اللون للأخضر")
assert not _co.EDIT.search("تمام شكرا يا جماعة") and _co.EDIT.match("عدل علي موقع الكافيه وخليه احلا")

# auto: each job gets its own chain; a provider without a key is skipped
from weblume import config as _cfg  # noqa: E402
assert set(_cfg.JOBS) == {"code", "write", "fast"} and all(s.split(":")[0] in _cfg._KEYS for v in _cfg.JOBS.values() for s in v)

# No grey boxes: every photo placeholder gets a stand-in photo saved with the site
_d = Path(tempfile.mkdtemp())
_fake = lambda prompt, out, w, h: (out.parent.mkdir(parents=True, exist_ok=True), out.write_bytes(b"x"), True)[2]
_html, _n = templates.fill_photos(templates.load("fresh"), _d, "مطعم", make=_fake)
assert _n == _html.count('src="img/photo-') == 8 and (_d / "img" / "photo-1.jpg").is_file()

print("All rule checks passed.")
