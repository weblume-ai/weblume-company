"""Hassan's free video mode: a vertical 9:16 video drawn by player.html, captured frame by frame in the
installed Chrome and encoded to MP4 with ffmpeg. Text scenes, Weblume branding, and our websites scrolling
inside phone / laptop mockups."""
import functools
import json
import shutil
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
TRANSITIONS = ("wipe", "zoom", "flip", "slide", "iris", "split", "shutter", "rise", "glitch")  # how a scene enters; player.html draws them
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
        if sc.get("type") not in ("hook", "text", "site", "cta", "image", "kinetic", "counter", "logo", "photos"):
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
    out = {"title": str(spec.get("title") or "Weblume"), "website": WEBSITE, "scenes": scenes}
    if isinstance(spec.get("style"), dict):  # set by the code from a reference reel, never trusted raw
        out["style"] = clean_style(spec["style"])
    return out


FONTS = ("Alexandria", "Cairo", "Tajawal", "IBM Plex Sans Arabic", "Readex Pro", "Almarai", "Changa", "Lalezar")
STYLE_PROMPT = """These are frames from a short vertical video, in order ({n} frames, one every {gap:.1f} s; it has {cuts} cuts
in {dur:.0f} s). A motion designer will copy its STYLE (not its words, logos or footage) for a new reel. Describe the
look so it can be rebuilt with text, photos and phone mockups. Answer with JSON only:
{{"bg": "#hex main background", "text": "#hex main text colour", "accent": "#hex the one highlight colour",
  "font": one of {fonts} closest to its headline type, "weight": 400-900, "align": "center" or "right",
  "glow": true/false (soft coloured light behind things), "grain": 0-1 (film texture), "photo": "full" (photos fill the
  screen) or "card" (photos in rounded cards), "words": "slam" (big words one at a time) or "lines" (whole lines rise),
  "transitions": the entrances it uses, ordered by how often, from {trs},
  "notes": "2-3 sentences: layout, type sizes, how things move, the rhythm, what makes it feel like this"}}"""


def take_reference():
    """On a video run, the newest video the owner uploaded is the reel whose style to copy. It moves out of the inbox
    (to output/uploads/references) before anything else runs, so the factory never takes it as a client's footage."""
    from ..uploads import INBOX
    vids = [p for p in INBOX.glob("*") if p.suffix.lower() in (".mp4", ".mov", ".webm", ".m4v")] if INBOX.exists() else []
    if not vids:
        return None
    ref = max(vids, key=lambda p: p.name)
    keep = ROOT / "output" / "uploads" / "references"
    keep.mkdir(parents=True, exist_ok=True)
    return Path(shutil.move(str(ref), str(keep / ref.name)))


def read_style(ref: Path) -> dict:
    """What a reference reel looks like (colours, type, transitions, pace), read by a vision model from its frames and
    cut times. Saved next to the video, so the brief and the render read it once."""
    import re
    import imageio_ffmpeg
    from .. import tester
    cache = ref.with_suffix(ref.suffix + ".style.json")
    if cache.is_file():
        return json.loads(cache.read_text(encoding="utf-8"))
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    log = subprocess.run([ff, "-i", str(ref), "-vf", "select='gt(scene,0.3)',showinfo", "-an", "-f", "null", "-"],
                         capture_output=True, text=True, errors="replace").stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", log)
    dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 15.0
    cuts = len(re.findall(r"pts_time:", log))
    n = 10
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([ff, "-v", "error", "-i", str(ref), "-vf", f"fps={n / dur:.4f},scale=540:-2", "-frames:v", str(n),
                        str(Path(tmp) / "f%02d.jpg")], check=True)
        frames = sorted(Path(tmp).glob("f*.jpg"))
        raw, _ = tester.look(frames, STYLE_PROMPT.format(n=len(frames), gap=dur / n, cuts=cuts, dur=dur, fonts=list(FONTS),
                                                          trs=list(TRANSITIONS)), lambda d: bool(d.get("bg")))
    style = clean_style(raw)
    style["shot"] = round(max(.8, min(5, dur / (cuts + 1))), 1)  # seconds per shot in the reference: its pace
    cache.write_text(json.dumps(style, ensure_ascii=False, indent=1), encoding="utf-8")
    return style


def clean_style(d: dict) -> dict:
    """Only values the player can draw: hex colours, a known font, known transitions."""
    import re
    hexc = lambda v, dflt: v if isinstance(v, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", v.strip()) else dflt
    trs = [t for t in (d.get("transitions") or []) if t in TRANSITIONS][:4]
    try:
        weight = max(400, min(900, int(d.get("weight") or 800) // 100 * 100))
    except (TypeError, ValueError):
        weight = 800
    return {"bg": hexc(d.get("bg"), "#0a0a0a"), "text": hexc(d.get("text"), "#ffffff"), "accent": hexc(d.get("accent"), "#e50914"),
            "font": d.get("font") if d.get("font") in FONTS else "Alexandria", "weight": weight,
            "align": "right" if d.get("align") == "right" else "center", "glow": d.get("glow") is not False,
            "grain": max(0.0, min(1.0, float(d.get("grain") or 0) if isinstance(d.get("grain"), (int, float)) else .5)),
            "photo": "card" if d.get("photo") == "card" else "full", "words": "lines" if d.get("words") == "lines" else "slam",
            "transitions": trs or list(TRANSITIONS), "notes": str(d.get("notes") or "")[:600]}


def real_photos(spec: dict) -> list[Path]:
    """The biggest photos of the client site this reel shows (its img/ folder), for the image scenes: real food, not AI."""
    site = next((s["site"] for s in spec["scenes"] if s.get("type") == "site"), None)
    folder = ROOT / "output" / str(site) / "img"
    if not site or not folder.is_dir():
        return []
    return sorted((p for p in folder.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")),
                  key=lambda p: -p.stat().st_size)[:8]


REVIEW_PROMPT = """You are a strict motion-design reviewer. These are frames of a vertical reel, two per scene (just after it
enters, and in its middle), in order. The scenes:
{scenes}
Find what a viewer would notice: text cut off or touching the edge, text hard to read on its background, Arabic broken
or reversed, a black or empty frame, a photo that doesn't match the words, two scenes that look the same, a boring
stretch, a wrong or repeated entrance. Ignore the Weblume logo at the top. Answer JSON only:
{{"problems": [{{"scene": number, "problem": "...", "fix": {{only the fields to change: "text", "sub", "caption", "dur",
"in" (one of {trs}), "type" ("text" to replace a weak scene)}}}}]}}
Max 5 problems, only real ones; an empty list if the reel is good."""


def review(mp4: Path, spec: dict) -> list[dict]:
    """A vision model watches frames of the finished reel and returns problems with scene fixes (empty when it's good)."""
    import imageio_ffmpeg
    from .. import tester
    t, times, lines = 0.0, [], []
    for i, sc in enumerate(spec["scenes"]):
        d = max(1.5, min(8, float(sc.get("dur") or 3)))  # the player's own rule
        times += [t + .7, t + d / 2 + .3]
        lines.append(f"{i}: {sc['type']} {json.dumps({k: sc[k] for k in ('text', 'sub', 'caption', 'in') if sc.get(k)}, ensure_ascii=False)}")
        t += d
    with tempfile.TemporaryDirectory() as tmp:
        for k, at in enumerate(times):
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-ss", f"{at:.2f}", "-i", str(mp4), "-frames:v", "1",
                            "-vf", "scale=360:-2", str(Path(tmp) / f"r{k:02d}.jpg")], check=False)
        frames = sorted(Path(tmp).glob("r*.jpg"))
        data, _ = tester.look(frames, REVIEW_PROMPT.format(scenes=chr(10).join(lines), trs=list(TRANSITIONS)),
                              lambda d: isinstance(d.get("problems"), list))
    return [p for p in data["problems"][:5] if isinstance(p, dict) and isinstance(p.get("scene"), int)]


def apply_fixes(spec: dict, problems: list[dict]) -> dict:
    """The reviewer's fixes, limited to wording, timing, entrance and swapping a weak scene for a text line."""
    scenes = [dict(sc) for sc in spec["scenes"]]
    for p in problems:
        if 0 <= p["scene"] < len(scenes) - 1 and isinstance(p.get("fix"), dict):  # never the closing Weblume scene
            fix = {k: v for k, v in p["fix"].items() if k in ("text", "sub", "caption", "dur", "in")
                   or (k == "type" and v == "text")}
            scenes[p["scene"]].update(fix)
    for a, b in zip(scenes, scenes[1:]):  # a fix must not give two scenes in a row the same entrance
        if b.get("in") and b.get("in") == a.get("in"):
            b.pop("in")
    return clean_spec({**spec, "scenes": scenes}, built_sites())


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


def _open(page, url: str):
    """Open a page; a slow web font or photo only delays it: after 60 s carry on with what has loaded (the player waits
    for its own frames and fonts in window.ready) instead of failing the whole video."""
    try:
        page.goto(url, wait_until="load", timeout=60000)
    except Exception as e:
        if "Timeout" not in type(e).__name__ + str(e):
            raise
        page.wait_for_load_state("domcontentloaded")


def capture_site(browser, url: str, out: Path, laptop: bool, dur: float, nth: int = 0) -> int:
    """Screenshots of a site scrolling from its hero to ~70% down, one per video frame. nth: the how-many-th time
    this reel films the site, so a paged menu opens another page instead of showing the same one twice."""
    out.mkdir(parents=True, exist_ok=True)
    size = {"width": 1440, "height": 900} if laptop else {"width": 390, "height": 844}
    page = browser.new_page(viewport=size, is_mobile=not laptop, has_touch=not laptop, device_scale_factor=1 if laptop else 2)
    _open(page, url)
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
                    if sc["type"] == "photos":  # needs the client's real product photos; without them it's a text line
                        sc["n"] = min(3, len(real))
                        for j in range(sc["n"]):
                            (tmp / "frames").mkdir(parents=True, exist_ok=True)
                            (tmp / "frames" / f"ph{i}_{j}.jpg").write_bytes(real.pop(0).read_bytes())
                        if not sc["n"]:
                            sc.update(type="text", text=sc.get("caption") or "Weblume")
                    if sc["type"] == "site":
                        seen[sc["site"]] = seen.get(sc["site"], -1) + 1
                        sc["frames"] = capture_site(browser, f"{base_url}/output/{quote(sc['site'])}/index.html",
                                                    tmp / "frames" / str(i), sc.get("device") == "laptop", float(sc.get("dur") or 3),
                                                    seen[sc["site"]])
                (tmp / "spec.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
                # 2) draw the video frame by frame
                page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
                _open(page, f"{base_url}/player.html")
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
