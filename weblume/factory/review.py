"""Automatic review of a factory site in a real browser (installed Chrome via Playwright), at 360, 768 and 1280 px:
console errors, sideways scroll, images that don't load, WhatsApp links, the map. Screenshots go to <site>/_review/."""
import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SIZES = [("phone", 360, 780), ("tablet", 768, 1024), ("desktop", 1280, 800)]


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def check(site: Path) -> tuple[list[str], list[str]]:
    """Returns (issues, screenshot paths). An empty issue list means the site passed."""
    from playwright.sync_api import sync_playwright
    srv = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(site)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url, out, issues, shots = f"http://127.0.0.1:{srv.server_address[1]}/", site / "_review", [], []
    out.mkdir(exist_ok=True)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome")
            for name, w, h in SIZES:
                pg = b.new_page(viewport={"width": w, "height": h}, is_mobile=w < 700, has_touch=w < 700)
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.on("console", lambda m: m.type == "error" and "favicon" not in m.text and errs.append(m.text))
                pg.goto(url, wait_until="load", timeout=60000)
                pg.wait_for_timeout(1500)
                total = pg.evaluate("document.documentElement.scrollHeight")
                for i, f in enumerate((0, .12, .3, .5, .7, .9)):  # scroll through so lazy images load and scenes play
                    pg.evaluate(f"scrollTo(0, {total} * {f})")
                    pg.wait_for_timeout(900)
                    if name != "tablet" and i in (0, 2, 3, 5):
                        shot = out / f"{name}_{i}.png"
                        pg.screenshot(path=str(shot))
                        shots.append(str(shot))
                pg.wait_for_timeout(800)
                wide = pg.evaluate("document.documentElement.scrollWidth - innerWidth")
                if wide > 1:
                    issues.append(f"OVERFLOW {name}: the page scrolls sideways by {wide}px")
                for src in pg.evaluate("[...document.images].filter(i => i.complete && !i.naturalWidth).map(i => i.getAttribute('src'))"):
                    issues.append(f"BROKEN {src} ({name})")
                bad_wa = pg.evaluate("[...document.querySelectorAll('a[href*=\"wa.me\"]')].filter(a => !/wa\\.me\\/\\d{10,15}/.test(a.href)).length")
                if bad_wa:
                    issues.append(f"WHATSAPP {name}: {bad_wa} link(s) without a valid number")
                if pg.evaluate("!!document.querySelector('iframe[src*=\"google.com/maps\"], iframe[src*=\"maps.google\"]')"):
                    issues.append(f"MAP {name}: an embedded Google map is on the page; the owner never wants one (use the directions button)")
                issues += [f"CONSOLE {name}: {e[:200]}" for e in dict.fromkeys(errs)]
                pg.close()
            b.close()
    finally:
        srv.shutdown()
    return list(dict.fromkeys(issues)), shots
