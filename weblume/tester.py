"""Tarek, the tester: opens the finished site in real Chrome like a visitor, scrolls it on desktop and phone,
and has Gemini look at the screenshots and judge whether it's good enough to show a client."""
import functools
import json
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import rules
from .config import CallTimeout, PROVIDER, _calls, model_name

PASS_SCORE = 8
TEMPLATE_NOTES = {  # what Tarek must know about Weblume's approved templates, so he doesn't flag their design
    "cafe": "This page is Weblume's approved animated template (the Loopie design). Its scroll scenes are intended and "
            "screenshots catch them mid-motion: a dark circle that opens onto a photo, a coffee bean that darkens as the "
            "temperature rises, drinks dropping into a colored disc, a sticky WhatsApp/directions bar on phones, round "
            "buttons. Do NOT report any of these. Only report what the CONTENT controls: wording, Arabic/English text, "
            "names, brand colors and their contrast, menu items and prices, photos chosen, missing information.",
}
DESKTOP = [0, .15, .3, .5, .7, .9]
PHONE = [0, .4, .8]


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def shoot(site_dir: Path, out_dir: Path, tag: str) -> list[Path]:
    """Screenshots of site_dir/index.html served over http (scroll scenes don't run from a file)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("Playwright is missing: run  .venv\\Scripts\\python -m pip install -r requirements.txt")
    out_dir.mkdir(parents=True, exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(site_dir)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url, shots = f"http://127.0.0.1:{srv.server_address[1]}/index.html", []
    try:
        with sync_playwright() as p:
            browser = None
            for channel in ("chrome", "msedge"):  # the visitor's real browser, no extra download
                try:
                    browser = p.chromium.launch(channel=channel)
                    break
                except Exception:
                    continue
            if not browser:
                raise RuntimeError("Tarek needs Google Chrome or Microsoft Edge installed.")
            for name, size, points, mobile in (("desktop", (1440, 900), DESKTOP, False), ("phone", (390, 844), PHONE, True)):
                page = browser.new_page(viewport={"width": size[0], "height": size[1]}, is_mobile=mobile, has_touch=mobile,
                                        device_scale_factor=1)
                page.goto(url, wait_until="load")
                page.wait_for_timeout(3500)  # opening animation, fonts
                height = page.evaluate("document.documentElement.scrollHeight - innerHeight")
                for i, f in enumerate(points):
                    page.evaluate(f"scrollTo(0, {height} * {f})")
                    page.wait_for_timeout(900)
                    path = out_dir / f"{tag}_{name}_{i + 1}.png"
                    page.screenshot(path=str(path))
                    shots.append(path)
                page.close()
            browser.close()
    finally:
        srv.shutdown()
    return shots


RUBRIC = """You are Tarek, a strict senior QA tester and art director at Weblume, a web design studio whose sites must
look hand-designed and premium (award-gallery quality), never generic or "AI-made".
These are screenshots of one website for this client brief:
\"\"\"{brief}\"\"\"
The first {nd} are the desktop page scrolled from top to bottom, the last {np} the same page on a phone.
Judge what a real visitor sees. Check: overall visual quality and polish; typography and spacing; Arabic text
right-to-left and readable; nothing overlapping, cut off or overflowing; no empty frames, broken images or blank
sections; the phone layout; the brand and the business are clear; call-to-action buttons visible. Things that look
AI-made and must be flagged: dark with gold, gradients everywhere, pill badges, stat counters, generic three-feature
lists, drawings made in code, fake reviews or ratings.
{notes}
Answer with JSON only:
{{"score": 0-10, "verdict": "PASS" or "FIX", "good": "one sentence on what works",
  "problems": [{{"where": "desktop 2 / phone 1 …", "problem": "…", "fix": "exact change"}}]}}
Score 8 or more only if you would show it to a paying client today. Max 6 problems, most important first."""


def judge(shots: list[Path], brief: str, notes: str = "") -> dict:
    """Gemini looks at the screenshots. Uses Gemini whenever GEMINI_API_KEY is set, even if the team runs on Groq/Ollama."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Tarek needs GEMINI_API_KEY in .env to look at the site.")
    from google import genai
    from google.genai import types

    nd = sum("_desktop_" in p.name for p in shots)
    parts = [types.Part.from_bytes(data=p.read_bytes(), mime_type="image/png") for p in shots]
    parts.append(RUBRIC.format(brief=brief, nd=nd, np=len(shots) - nd, notes=notes))
    first = model_name() if PROVIDER == "gemini" else "gemini-3.5-flash"
    models = [first, *[m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.8-flash,gemini-3.1-flash-lite").split(",")
                       if m.strip() and m.strip() != first]]
    client, last = genai.Client(api_key=key), None
    ask = lambda m: client.models.generate_content(model=m, contents=parts,
                                                  config=types.GenerateContentConfig(response_mime_type="application/json")).text
    jobs = [(m, lambda m=m: ask(m)) for m in models]
    jobs.append((LOCAL_VISION, lambda: _local_vision(shots, parts[-1])))  # gemma3 on the laptop sees images: no quota
    if os.getenv("GROQ_API_KEY", "").strip():  # when every Gemini model is out of quota, a Groq vision model looks instead
        jobs.append((GROQ_VISION, lambda: _groq_vision(shots, parts[-1])))
    for m, job in jobs:
        try:
            # the SDK waits as long as Gemini says ("retry in 20h" on a used-up quota): give each model 90 s, then move on
            data = rules.extract_json(_calls.submit(job).result(timeout=360 if m == LOCAL_VISION else 90))  # the laptop is slower, never out of quota
            if isinstance(data, dict) and "score" in data:
                data["score"] = float(data["score"])
                data["verdict"] = "PASS" if data["score"] >= PASS_SCORE else "FIX"
                data["model"] = m
                return data
            last = RuntimeError("Tarek's answer was not in the expected format.")
        except CallTimeout:
            last = RuntimeError(f"{m} gave no answer in 90 s (probably out of free quota)")
        except Exception as e:  # busy model: try the next one
            last = e
    raise RuntimeError(f"Tarek couldn't get a verdict: {last}")


GROQ_VISION = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
LOCAL_VISION = os.getenv("LOCAL_VISION_MODEL", "gemma3:12b")


def _local_vision(shots: list[Path], prompt: str) -> str:
    """The same question to a vision model in Ollama on this laptop: 4 screenshots, shrunk to 768 px JPEGs to keep it quick."""
    import base64
    import io
    import json as _json
    import urllib.request
    from PIL import Image

    def small(p):
        with Image.open(p) as im:
            im = im.convert("RGB")
            im.thumbnail((768, 768))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=80)
        return base64.b64encode(buf.getvalue()).decode()

    body = {"model": LOCAL_VISION, "stream": False, "format": "json", "options": {"num_ctx": 8192},
            "messages": [{"role": "user", "content": prompt, "images": [small(p) for p in shots[:4]]}]}
    req = urllib.request.Request(os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/") + "/api/chat",
                                 data=_json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=350) as r:
        return _json.loads(r.read())["message"]["content"]


def _groq_vision(shots: list[Path], prompt: str) -> str:
    """The same question to a Groq vision model (OpenAI format, screenshots as base64). At most 5 images per request."""
    import base64
    import json as _json
    import urllib.request
    content = [{"type": "text", "text": prompt}] + [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()}}
        for p in shots[:5]]
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", method="POST",
                                 data=_json.dumps({"model": GROQ_VISION, "messages": [{"role": "user", "content": content}],
                                                   "response_format": {"type": "json_object"}}).encode(),
                                 headers={"Authorization": "Bearer " + os.getenv("GROQ_API_KEY", "").strip(),
                                          "Content-Type": "application/json", "User-Agent": "weblume-company"})
    with urllib.request.urlopen(req, timeout=80) as r:
        return _json.loads(r.read())["choices"][0]["message"]["content"]


def report(result: dict) -> str:
    lines = [f"# Tarek's test: {result['score']:g}/10 · {result['verdict']}", "", result.get("good", ""), ""]
    for i, p in enumerate(result.get("problems") or [], 1):
        lines.append(f"{i}. **{p.get('where', '')}**: {p.get('problem', '')} → {p.get('fix', '')}")
    return "\n".join(lines)
