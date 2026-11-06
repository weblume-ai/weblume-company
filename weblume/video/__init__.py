"""Hassan's free video mode: a vertical 9:16 video drawn by player.html, captured frame by frame in the
installed Chrome and encoded to MP4 with ffmpeg. Text scenes, Weblume branding, and our websites scrolling
inside phone / laptop mockups."""
import functools
import json
import subprocess
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote

from .. import rules
from ..config import ROOT, WEBSITE

PLAYER = Path(__file__).parent / "player.html"
FPS = 24
ALLOWED = ("/knowledge/brand/", "/output/", "/spec.json", "/player.html", "/frames/")


def clean_spec(spec: dict, sites: list[str]) -> dict:
    """Keep only scenes we can draw, never a phone number, always end on 'contact us through the Weblume website'."""
    scenes = []
    for sc in (spec.get("scenes") or [])[:10]:
        if not isinstance(sc, dict):
            continue
        sc = {k: v for k, v in sc.items() if k in ("type", "text", "sub", "caption", "site", "device", "dur")}
        for k in ("text", "sub", "caption"):
            if isinstance(sc.get(k), str) and rules.remove_phone_numbers(sc[k])[1]:
                sc[k] = "تواصل معانا من موقع Weblume"  # a line that carried a phone number is replaced whole
        if sc.get("type") == "site" and sc.get("site") not in sites:
            if not sites:
                continue
            sc["site"] = sites[0]
        if sc.get("type") not in ("hook", "text", "site", "cta"):
            sc["type"] = "text"
        scenes.append(sc)
    scenes = [s for s in scenes if s["type"] != "cta"]
    scenes.append({"type": "cta", "text": "تواصل معانا من موقع Weblume", "dur": 3})
    total = sum(max(1.5, min(8, float(s.get("dur") or 3))) for s in scenes)
    if total > 45:  # short-form: keep it under ~45s
        for s in scenes:
            s["dur"] = max(1.5, float(s.get("dur") or 3) * 45 / total)
    return {"title": str(spec.get("title") or "Weblume"), "website": WEBSITE, "scenes": scenes}


def built_sites() -> list[str]:
    out = ROOT / "output"
    return sorted(p.name for p in out.iterdir() if (p / "index.html").is_file() and p.name != "runs") if out.exists() else []


def capture_site(browser, url: str, out: Path, laptop: bool, dur: float) -> int:
    """Screenshots of a site scrolling from its hero to ~70% down, one per video frame."""
    out.mkdir(parents=True, exist_ok=True)
    size = {"width": 1440, "height": 900} if laptop else {"width": 390, "height": 844}
    page = browser.new_page(viewport=size, is_mobile=not laptop, has_touch=not laptop, device_scale_factor=1 if laptop else 2)
    page.goto(url, wait_until="load")
    page.wait_for_timeout(3000)
    top, end = page.evaluate("[innerHeight * .45, (document.documentElement.scrollHeight - innerHeight) * .7]")
    for f in (.25, .5, .75, 1, 0):  # warm up: let lazy photos and scroll frames load
        page.evaluate(f"scrollTo(0, {top + (end - top) * f})")
        page.wait_for_timeout(700)
    n = max(1, int(dur * FPS))
    for k in range(n):
        x = k / max(1, n - 1)
        e = x * x * (3 - 2 * x)  # smoothstep: start and stop gently
        page.evaluate(f"scrollTo(0, {top + (end - top) * e})")
        page.wait_for_timeout(45)
        page.screenshot(path=str(out / f"{k:04d}.jpg"), type="jpeg", quality=88)
    page.close()
    return n


def render(spec: dict, out_mp4: Path, progress=lambda f: None) -> Path:
    """Draw every frame of the spec and encode it. progress(fraction) is called as frames are captured."""
    from playwright.sync_api import sync_playwright
    import imageio_ffmpeg

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
        ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS),
                               "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", str(out_mp4)],
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
                for i, sc in enumerate(spec["scenes"]):
                    if sc["type"] == "site":
                        sc["frames"] = capture_site(browser, f"{base_url}/output/{quote(sc['site'])}/index.html",
                                                    tmp / "frames" / str(i), sc.get("device") == "laptop", float(sc.get("dur") or 3))
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
