"""Tarek, the tester: opens the finished site in real Chrome like a visitor, scrolls it on desktop and phone,
and has Gemini look at the screenshots and judge whether it's good enough to show a client."""
import functools
import json
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import rules
from .config import model_name, PROVIDER

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
    for m in models:
        try:
            r = client.models.generate_content(model=m, contents=parts,
                                               config=types.GenerateContentConfig(response_mime_type="application/json"))
            data = rules.extract_json(r.text)
            if isinstance(data, dict) and "score" in data:
                data["score"] = float(data["score"])
                data["verdict"] = "PASS" if data["score"] >= PASS_SCORE else "FIX"
                data["model"] = m
                return data
            last = RuntimeError("Tarek's answer was not in the expected format.")
        except Exception as e:  # busy model: try the next one
            last = e
    raise RuntimeError(f"Tarek couldn't get a verdict: {last}")


def report(result: dict) -> str:
    lines = [f"# Tarek's test: {result['score']:g}/10 · {result['verdict']}", "", result.get("good", ""), ""]
    for i, p in enumerate(result.get("problems") or [], 1):
        lines.append(f"{i}. **{p.get('where', '')}**: {p.get('problem', '')} → {p.get('fix', '')}")
    return "\n".join(lines)
