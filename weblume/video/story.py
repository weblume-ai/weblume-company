"""The story reel: Weblume's approved café ad (weblume-ad/cafe, «الكافيه بتاعك») as a template. Its timing, camera,
synthesized sound and look stay exactly as approved; Hassan writes the words for each client and the code films the
client's own site into the phone and puts the shop's real items on the paper menu.

Story: paper menu → crossed-out items and reprints → unanswered chat → QR → the real site in a phone → the offer
→ the Weblume end card. It fits any shop with a menu (cafés, restaurants, sweets, juice bars)."""
import functools
import json
import shutil
import subprocess
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .. import config, rules
from ..config import ROOT

TEMPLATE = Path(__file__).parent / "story"
DURATION = 30  # the approved film's length; its sound (mix.m4a) is synced to it beat by beat
# The approved ad's own words: every line Hassan leaves out keeps these. *word* = drawn in red.
DEFAULT = {
    "hook1": "المنيو الورق", "hook2": "بيخسّرك زباين.",
    "items": ["V60", "كورتادو", "سبانش لاتيه", "فلات وايت", "كولد برو", "ليمون نعناع"],
    "paper1": "صنف خلص؟ اتشطب *بالقلم.*", "paper2": "اتغيّر حاجة؟ اطبع *من* الأول.", "stamp": "طبعة جديدة؟ تاني؟",
    "chat_to": "رسالة لصفحة المحل", "ask1": "عندكم إيه النهارده؟", "ask2": "ممكن صور للأصناف؟", "noreply": "مفيش رد…",
    "qr_line": "خلّيه *يمسح…* ويشوف كل حاجة.", "qr_title": "امسح وشوف المنيو", "qr_sub": "المنيو كله بالصور",
    "phone": ["ده شغل من *تصميمنا*", "المنيو كله *بالصور*", "يقلّب… *ويختار*", "أي تعديل… من *غير* طباعة", "باسم *محلك…* وبهويته"],
    "offer": ["تشوف التصميم الأول", "قبل ما تدفع", "موقع باسم محلك", "مش قالب جاهز"],
    "end1": "كلّمنا من الموقع اللي في البايو", "end2": "وكمان نعملك فيديو إعلاني لمحلك",
}
LIMITS = {"hook1": 22, "hook2": 22, "paper1": 34, "paper2": 34, "stamp": 22, "chat_to": 30, "ask1": 24, "ask2": 24,
          "noreply": 14, "qr_line": 34, "qr_title": 22, "qr_sub": 26, "end1": 40, "end2": 40}


def clean_story(raw: dict) -> dict:
    """Hassan's lines over the approved defaults: strings only, short enough for the film's layout, no phone numbers."""
    out = json.loads(json.dumps(DEFAULT))
    ok = lambda v, n: isinstance(v, str) and 0 < len(v.strip()) <= n and not rules.remove_phone_numbers(v)[1]
    for k, n in LIMITS.items():
        if ok(raw.get(k), n):
            out[k] = raw[k].strip()
    for k, n, size in (("phone", 34, 5), ("offer", 22, 4)):
        v = raw.get(k)
        if isinstance(v, list) and len(v) == size and all(ok(x, n) for x in v):
            out[k] = [x.strip() for x in v]
    for k in LIMITS:  # only the captions draw a *starred* word in red; elsewhere a star would show as a star
        if k not in ("paper1", "paper2", "qr_line"):
            out[k] = out[k].replace("*", "")
    items = [x.strip() for x in raw.get("items") or [] if ok(x, 20)]
    if len(items) >= 2:
        out["items"] = items[:6]
    return out


# the site's own menu item names (cards, headings), its credit line, and how to page through it
SITE_JS = """() => {
  const seen = new Set(), items = [];
  for (const e of document.querySelectorAll('h3, h4, [class*=name], [class*=title] b, figcaption')) {
    const t = (e.innerText || '').trim().split('\\n')[0];
    if (t && t.length <= 20 && /[\\u0600-\\u06FF]/.test(t) && !seen.has(t)) { seen.add(t); items.push(t) }
  }
  const credit = [...document.querySelectorAll('body *')].find(e => !e.children.length && /Weblume/i.test(e.textContent || '')
    && e.getBoundingClientRect().top > innerHeight * .6 && e.getBoundingClientRect().bottom <= innerHeight);
  const r = credit && credit.getBoundingClientRect();
  return {items: items.slice(0, 8), credit: r ? (r.top + r.height / 2) / innerHeight : null,
          paged: document.documentElement.scrollHeight <= innerHeight + 10 && !!document.querySelector('[data-go]')};
}"""


def film_pages(browser, url: str, out: Path) -> dict:
    """Six phone screens of the site (the cover, then its pages or scroll stops), the real item names and the
    cover's credit line, for the phone shot."""
    from PIL import Image, ImageStat
    from . import _open
    out.mkdir(parents=True, exist_ok=True)
    page = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2)
    _open(page, url)
    page.wait_for_timeout(2500)
    info = page.evaluate(SITE_JS)
    page.screenshot(path=str(out / "p0.jpg"), type="jpeg", quality=90)
    n = 1
    if info["paged"]:  # a paged menu: open each category from the cover, like a visitor swiping
        count = page.evaluate("document.querySelectorAll('[data-go]').length")
        for j in range(min(5, count)):
            _open(page, url)
            page.wait_for_timeout(1200)
            page.evaluate(f"document.querySelectorAll('[data-go]')[{j}].click()")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(out / f"p{n}.jpg"), type="jpeg", quality=90)
            n += 1
    else:  # a scrolling site: five stops down the page
        height = page.evaluate("document.documentElement.scrollHeight - innerHeight")
        for f in (.15, .32, .5, .68, .85):
            page.evaluate(f"scrollTo(0, {height * f})")
            page.wait_for_timeout(1300)
            page.screenshot(path=str(out / f"p{n}.jpg"), type="jpeg", quality=90)
            n += 1
    page.close()
    light = []
    for i in range(n):  # a light page top needs a dark status bar
        with Image.open(out / f"p{i}.jpg") as im:
            if ImageStat.Stat(im.convert("L").crop((0, 0, im.width, 120))).mean[0] > 150:
                light.append(i)
    return {"pages": n, "light": light, "items": info["items"], "credit_y": info["credit"]}


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def render_story(lines: dict, site: str, out_mp4: Path, progress=lambda f: None) -> Path:
    """Film the story reel for one of our sites (output/<site>) with Hassan's lines; MP4 with the approved sound."""
    from playwright.sync_api import sync_playwright
    import imageio_ffmpeg
    from . import _open
    fps = config.level()["fps"]
    story = clean_story(lines)
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "film"
        shutil.copytree(TEMPLATE, work)
        srv = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(Path(tmp))))
        site_dir = Path(tmp) / "site"
        shutil.copytree(ROOT / "output" / site, site_dir)  # served beside the film: one local server, no internet needed
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        try:
            with sync_playwright() as p:
                browser = None
                for channel in ("chrome", "msedge"):
                    try:
                        browser = p.chromium.launch(channel=channel)
                        break
                    except Exception:
                        continue
                if not browser:
                    raise RuntimeError("Hassan needs Google Chrome or Microsoft Edge installed.")
                shot = film_pages(browser, f"{base}/site/index.html", work / "pages")
                if len(shot["items"]) >= 2:  # the shop's real items from its own site win over anything written
                    story["items"] = shot["items"][:6]
                story.update(pages=shot["pages"], light=shot["light"], credit_y=shot["credit_y"])
                (work / "story.json").write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")
                page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                _open(page, f"{base}/film/index.html?render=1&format=9x16&fps={fps}")
                page.wait_for_function("window.filmReady === true", timeout=90000)
                if errors:
                    raise RuntimeError("The story film failed: " + errors[0])
                out_mp4.parent.mkdir(parents=True, exist_ok=True)
                ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "image2pipe",
                                       "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-", "-i", str(work / "mix.m4a"),
                                       "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow",
                                       "-crf", str(config.level()["crf"]), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                                       "-shortest", "-movflags", "+faststart", str(out_mp4)], stdin=subprocess.PIPE)
                try:
                    frames = DURATION * fps
                    canvas = page.locator("#film")
                    for i in range(frames):
                        page.evaluate(f"window.seek({i / fps})")
                        ff.stdin.write(canvas.screenshot(type="jpeg", quality=94))
                        if i % fps == 0:
                            progress(i / frames)
                finally:
                    ff.stdin.close()
                    ff.wait()
                browser.close()
        finally:
            srv.shutdown()
    if ff.returncode != 0 or not out_mp4.is_file():
        raise RuntimeError("ffmpeg couldn't write the story reel.")
    return out_mp4
