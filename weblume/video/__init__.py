"""Hassan's free video mode: a vertical 9:16 video drawn by player.html, captured frame by frame in the
installed Chrome and encoded to MP4 with ffmpeg. Text scenes, Weblume branding, and our websites scrolling
inside phone / laptop mockups."""
import functools
import json
import subprocess
import urllib.request
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote

from .. import rules
from .. import config
from ..config import ROOT, WEBSITE

PLAYER = Path(__file__).parent / "player.html"
TRANSITIONS = ("wipe", "zoom", "slide", "iris", "shutter", "glitch")  # how a scene enters; player.html draws them
MUSIC = ROOT / "knowledge" / "brand" / "music.m4a"  # the bed from Weblume's approved kinetic reel
ALLOWED = ("/knowledge/brand/", "/output/", "/spec.json", "/player.html", "/frames/")


def clean_spec(spec: dict, sites: list[str]) -> dict:
    """Keep only scenes we can draw, never a phone number, always end on 'contact us through the Weblume website'."""
    scenes = []
    for sc in (spec.get("scenes") or [])[:10]:
        if not isinstance(sc, dict):
            continue
        sc = {k: v for k, v in sc.items() if k in ("type", "text", "sub", "caption", "site", "device", "dur", "prompt", "in")}
        if sc.get("in") not in TRANSITIONS:
            sc.pop("in", None)  # the player picks a different one for each scene
        for k in ("text", "sub", "caption"):
            if isinstance(sc.get(k), str) and rules.remove_phone_numbers(sc[k])[1]:
                sc[k] = "تواصل معانا من موقع Weblume"  # a line that carried a phone number is replaced whole
        if sc.get("type") == "site" and sc.get("site") not in sites:
            if not sites:
                continue
            sc["site"] = sites[0]
        if sc.get("type") == "image" and not str(sc.get("prompt") or "").strip():
            sc["type"] = "text"
        if sc.get("type") == "counter" and not any(ch.isdigit() for ch in str(sc.get("text") or "")):
            sc["type"] = "text"  # a counter needs a real number
        if sc.get("type") not in ("hook", "text", "site", "cta", "image", "kinetic", "counter", "logo"):
            sc["type"] = "text"
        if sc["type"] == "kinetic":  # the wipe, then at least half a second per word, or the words can't be read
            sc["dur"] = max(float(sc.get("dur") or 3), round(.8 + .5 * len(str(sc.get("text") or "").split()), 1))
        scenes.append(sc)
    scenes = [s for s in scenes if s["type"] != "cta"]
    scenes.append({"type": "cta", "text": "تواصل معانا من موقع Weblume", "dur": 3})
    total = sum(max(1.5, min(8, float(s.get("dur") or 3))) for s in scenes)
    if total > 45:  # short-form: keep it under ~45s
        for s in scenes:
            s["dur"] = max(1.5, float(s.get("dur") or 3) * 45 / total)
    return {"title": str(spec.get("title") or "Weblume"), "website": WEBSITE, "scenes": scenes}


def real_photos(spec: dict) -> list[Path]:
    """The biggest photos of the client site this reel shows (its img/ folder), for the image scenes: real food, not AI."""
    site = next((s["site"] for s in spec["scenes"] if s.get("type") == "site"), None)
    folder = ROOT / "output" / str(site) / "img"
    if not site or not folder.is_dir():
        return []
    return sorted((p for p in folder.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")),
                  key=lambda p: -p.stat().st_size)[:5]


def built_sites() -> list[str]:
    out = ROOT / "output"
    return sorted(p.name for p in out.iterdir() if (p / "index.html").is_file() and p.name != "runs") if out.exists() else []


def ai_image(prompt: str, out: Path, width: int = 1080, height: int = 1920) -> bool:
    """A free AI photo: FLUX on Cloudflare when its keys are set, else Pollinations (no key). False if none came back."""
    from ..factory.media import flux
    img = flux(prompt)
    if img:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(img)
        return True
    url = ("https://image.pollinations.ai/prompt/" + quote(prompt[:400]) +
           f"?width={width}&height={height}&nologo=true&seed={abs(hash(prompt)) % 100000}")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=120) as r:
            data = r.read()
            if not r.headers.get("Content-Type", "").startswith("image/") or len(data) < 5000:
                return False
    except Exception:
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return True


def capture_site(browser, url: str, out: Path, laptop: bool, dur: float, nth: int = 0) -> int:
    """Screenshots of a site scrolling from its hero to ~70% down, one per video frame. nth: the how-many-th time
    this reel films the site, so a paged menu opens another page instead of showing the same one twice."""
    out.mkdir(parents=True, exist_ok=True)
    size = {"width": 1440, "height": 900} if laptop else {"width": 390, "height": 844}
    page = browser.new_page(viewport=size, is_mobile=not laptop, has_touch=not laptop, device_scale_factor=1 if laptop else 2)
    page.goto(url, wait_until="load")
    page.wait_for_timeout(3000)
    # a menu app scrolls inside its visible page, not the window: film whatever really scrolls on screen
    find = """window.__sc = document.documentElement.scrollHeight > innerHeight + 10 ? null : [...document.querySelectorAll('*')]
      .filter(e => e.scrollHeight > e.clientHeight + 50 && /(auto|scroll)/.test(getComputedStyle(e).overflowY)
                   && (r => r.width > 0 && r.bottom > 0 && r.top < innerHeight && r.left < innerWidth && r.right > 0)(e.getBoundingClientRect()))
      .sort((a, b) => b.clientHeight - a.clientHeight)[0] || null;
      window.__to = y => window.__sc ? (window.__sc.scrollTop = y) : scrollTo(0, y);
      document.documentElement.scrollHeight > innerHeight + 10 || window.__sc"""
    span = "__sc ? [0, (__sc.scrollHeight - __sc.clientHeight) * .8] : [innerHeight * .45, (document.documentElement.scrollHeight - innerHeight) * .7]"
    moves = page.evaluate(find)
    # a paged menu whose cover doesn't scroll: show the cover, then open its first page (a [data-go] button) and scroll it
    tap = not moves and page.evaluate("!!document.querySelector('[data-go]')")
    top, end = page.evaluate(span)
    for f in (.25, .5, .75, 1, 0):  # warm up: let lazy photos and scroll frames load
        page.evaluate(f"__to({top + (end - top) * f})")
        page.wait_for_timeout(700)
    n = max(1, int(dur * config.level()["fps"]))
    for k in range(n):
        if tap and k == n // 3:
            page.evaluate(f"(b => b[{nth} % b.length].click())(document.querySelectorAll('[data-go]'))")
            page.wait_for_timeout(900)
            page.evaluate(find)
            top, end = page.evaluate(span)
        x = (k - n // 3) / max(1, n - 1 - n // 3) if tap and k >= n // 3 else (0 if tap else k / max(1, n - 1))
        e = x * x * (3 - 2 * x)  # smoothstep: start and stop gently
        page.evaluate(f"__to({top + (end - top) * e})")
        page.wait_for_timeout(45)
        page.screenshot(path=str(out / f"{k:04d}.jpg"), type="jpeg", quality=88)
    page.close()
    return n


def render(spec: dict, out_mp4: Path, progress=lambda f: None) -> Path:
    """Draw every frame of the spec and encode it. progress(fraction) is called as frames are captured."""
    from playwright.sync_api import sync_playwright
    import imageio_ffmpeg

    FPS, crf = config.level()["fps"], str(config.level()["crf"])
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "player.html").write_text(PLAYER.read_text(encoding="utf-8"), encoding="utf-8")

        class Files(SimpleHTTPRequestHandler):  # only the player, the spec, the brand folder and built sites
            def log_message(self, *_):
                pass

            def translate_path(self, path):
                p = unquote(path.split("?", 1)[0])
                base = tmp if p in ("/spec.json", "/player.html") or p.startswith("/frames/") else ROOT
                full = (base / p.lstrip("/")).resolve()
                if not p.startswith(ALLOWED) or base.resolve() not in full.parents:  # no .env, no ../
                    return str(tmp / "__nope__")
                return str(full)

        srv = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Files, directory=str(ROOT)))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        total = sum(max(1.5, min(8, float(s.get("dur") or 3))) for s in spec["scenes"])  # the player's own rule
        music = ["-stream_loop", "-1", "-i", str(MUSIC), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "128k", "-shortest",
                 "-af", f"afade=t=out:st={max(0, total - 1.2):.2f}:d=1.2"] if MUSIC.is_file() else []
        ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS),
                               "-i", "-", *music, "-c:v", "libx264", "-preset", "slow", "-pix_fmt", "yuv420p", "-crf", crf, "-movflags", "+faststart", str(out_mp4)],
                              stdin=subprocess.PIPE)
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
                base_url = f"http://127.0.0.1:{srv.server_address[1]}"
                # 1) film each site scrolling, slowly enough for its photos and scroll scenes to load
                real, seen = real_photos(spec), {}
                for i, sc in enumerate(spec["scenes"]):
                    if sc["type"] == "image":  # the client's real photo first, else an AI photo, else its caption as text
                        dest = tmp / "frames" / f"img{i}.jpg"
                        if real:
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            dest.write_bytes(real.pop(0).read_bytes())
                            sc["real"] = True
                        elif not ai_image(sc["prompt"], dest):
                            sc.update(type="text", text=sc.get("caption") or "Weblume")
                    if sc["type"] == "site":
                        seen[sc["site"]] = seen.get(sc["site"], -1) + 1
                        sc["frames"] = capture_site(browser, f"{base_url}/output/{quote(sc['site'])}/index.html",
                                                    tmp / "frames" / str(i), sc.get("device") == "laptop", float(sc.get("dur") or 3),
                                                    seen[sc["site"]])
                (tmp / "spec.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
                # 2) draw the video frame by frame
                page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
                page.goto(f"{base_url}/player.html", wait_until="load")
                page.evaluate("window.ready")
                total = page.evaluate("window.DURATION")
                frames = int(total * FPS)
                for i in range(frames):
                    page.evaluate(f"window.seek({i / FPS})")
                    ff.stdin.write(page.screenshot(type="png"))
                    if i % FPS == 0:
                        progress(i / frames)
                browser.close()
        finally:
            ff.stdin.close()
            ff.wait()
            srv.shutdown()
    if ff.returncode != 0 or not out_mp4.is_file():
        raise RuntimeError("ffmpeg couldn't write the video.")
    return out_mp4
