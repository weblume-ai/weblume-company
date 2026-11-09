"""Publish a finished site to GitHub Pages with the owner's own GitHub sign-in on this laptop.

Only runs when the owner presses "Publish" in the dashboard and confirms. Uses the token git already stores
(Git Credential Manager), or GITHUB_TOKEN from .env. The token never leaves this file's requests to api.github.com.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

OWNER = os.getenv("GITHUB_OWNER", "weblume-ai")  # the GitHub org (or user) that gets the new repos
API = "https://api.github.com"


def repo_name(text: str) -> str:
    """A safe GitHub repo name: lowercase latin letters, digits and dashes ('' if nothing is left)."""
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", text.lower())).strip("-")[:60]


def _token() -> str:
    if os.getenv("GITHUB_TOKEN"):
        return os.environ["GITHUB_TOKEN"]
    out = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True, timeout=60).stdout
    token = next((line[9:] for line in out.splitlines() if line.startswith("password=")), "")
    if not token:
        raise RuntimeError("No GitHub sign-in on this laptop. Sign in once with git (or put GITHUB_TOKEN in .env).")
    return token


def _call(method: str, path: str, token: str, body: dict | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                          "User-Agent": "weblume-company"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def _git(*args: str, cwd: Path) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=300)
    if r.returncode:
        raise RuntimeError(f"git {args[0]} failed: {(r.stderr or r.stdout).strip()[-300:]}")
    return r.stdout


def to_github(site_dir: Path, name: str, owner: str = OWNER) -> str:
    """Create (or update) github.com/<owner>/<name> with the site and turn on Pages. Returns the live URL."""
    name = repo_name(name)
    if not name:
        raise ValueError("The repo name needs English letters or numbers.")
    if not (site_dir / "index.html").is_file():
        raise ValueError("This run has no finished website to publish.")
    token = _token()
    code, me = _call("GET", "/user", token)
    if code != 200:
        raise RuntimeError("GitHub didn't accept the saved sign-in. Sign in again with git.")
    code, _ = _call("GET", f"/repos/{owner}/{name}", token)
    if code == 404:
        where = "/user/repos" if owner.lower() == me["login"].lower() else f"/orgs/{owner}/repos"
        code, res = _call("POST", where, token, {"name": name, "private": False, "auto_init": False,
                                                  "description": "Website by Weblume"})
        if code != 201:
            raise RuntimeError(f"GitHub refused to create the repo: {res.get('message', code)}")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "repo"
        _git("clone", "--depth", "1", f"https://github.com/{owner}/{name}.git", str(work), cwd=Path(tmp))
        for old in work.iterdir():  # the site replaces whatever was published before
            if old.name != ".git":
                shutil.rmtree(old) if old.is_dir() else old.unlink()
        shutil.copytree(site_dir, work, dirs_exist_ok=True)
        (work / ".nojekyll").write_text("", encoding="utf-8")  # serve files as they are
        _git("add", "-A", cwd=work)
        if _git("status", "--porcelain", cwd=work).strip():
            _git("commit", "-q", "-m", "Publish website", cwd=work)
            _git("push", "-q", "origin", "HEAD:main", cwd=work)
    code, res = _call("POST", f"/repos/{owner}/{name}/pages", token, {"source": {"branch": "main", "path": "/"}})
    if code not in (201, 409):  # 409 = Pages already on
        raise RuntimeError(f"The files are on GitHub but Pages didn't turn on: {res.get('message', code)}")
    return f"https://{owner.lower()}.github.io/{name}/"
