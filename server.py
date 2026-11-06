"""Weblume AI Company dashboard server (Python standard library only). Start with:  python server.py"""
import json
import os
import re
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from weblume import company, rules
from weblume.config import OUTPUT_DIR, PROVIDER, ROOT, model_name
from weblume.team import ORDER, TEAM

HOST, PORT = "127.0.0.1", 8501
PAGE = ROOT / "web" / "index.html"
LOCAL_HOST = re.compile(r"^(127\.0\.0\.1|localhost)(:\d+)?$", re.I)


def team_info():
    return [{"key": k, **{f: TEAM[k][f] for f in ("name", "role", "emoji")}} for k in ["layla", *ORDER]]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):  # keep the black window quiet
        pass

    def send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def local_only(self) -> bool:
        # Blocks other websites (and DNS-rebinding tricks) from driving the dashboard
        if not LOCAL_HOST.match(self.headers.get("Host", "")):
            self.send(403, {"error": "Local use only."})
            return False
        origin = self.headers.get("Origin")
        if self.command == "POST" and origin and not re.match(r"^http://(127\.0\.0\.1|localhost)(:\d+)?$", origin):
            self.send(403, {"error": "Local use only."})
            return False
        return True

    def do_GET(self):
        if not self.local_only():
            return
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        if url.path in ("/", "/index.html"):
            return self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        if url.path == "/api/state":
            try:
                contacted = rules.load_contacted()
            except RuntimeError as e:
                contacted, err = [], str(e)
            else:
                err = ""
            run = company.load_status(q["run"]) if q.get("run") else None
            return self.send(200, {"llm": f"{PROVIDER} / {model_name()}", "running": company.is_running(),
                                   "team": team_info(), "runs": company.list_runs()[:30], "run": run,
                                   "contacted": contacted, "contacted_error": err})
        if url.path == "/api/log" and q.get("run"):
            log = OUTPUT_DIR / "runs" / Path(q["run"]).name / "run.log"
            lines = log.read_text(encoding="utf-8").splitlines()[-200:] if log.exists() else []
            return self.send(200, {"lines": lines})
        if url.path == "/api/file" and q.get("path"):
            path = (OUTPUT_DIR / q["path"]).resolve()
            if OUTPUT_DIR.resolve() not in path.parents or not path.is_file():
                return self.send(404, {"error": "Not found."})
            if q.get("view") and path.suffix == ".html":
                # Generated sites run in their own sandboxed origin, so their scripts can't touch this dashboard
                return self.send(200, path.read_bytes(), "text/html; charset=utf-8",
                                 {"Content-Security-Policy": "sandbox allow-scripts allow-popups allow-forms"})
            return self.send(200, path.read_bytes(), "application/octet-stream",
                             {"Content-Disposition": f"attachment; filename*=UTF-8''{_quote(path.name)}"})
        self.send(404, {"error": "Not found."})

    def do_POST(self):
        if not self.local_only():
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > 100_000:
                return self.send(413, {"error": "Too big."})
            body = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/start":
                run_id = company.start(str(body.get("goal", "")), "focused" if body.get("mode") == "focused" else "whole",
                                       [str(k) for k in body.get("keys") or []], str(body.get("client", "")),
                                       str(body.get("names", "")).splitlines())
                return self.send(200, {"run": run_id})
            if self.path == "/api/contacted":
                biz = str(body.get("business", "")).strip()
                if not biz:
                    return self.send(400, {"error": "Business name is empty."})
                added = rules.mark_contacted(biz, str(body.get("city", "")), str(body.get("note", "")))
                return self.send(200, {"added": added})
            self.send(404, {"error": "Not found."})
        except (ValueError, RuntimeError) as e:
            self.send(400, {"error": str(e)})


def _quote(name: str) -> str:
    from urllib.parse import quote
    return quote(name)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print(f"\n  Weblume AI Company: {url}\n  AI model: {PROVIDER} / {model_name()}\n  Keep this window open. Close it to stop.\n")
    if not os.getenv("NO_BROWSER"):
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
