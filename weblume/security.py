"""Security scan of every finished site: fixes what is safe to fix, reports the rest (knowledge/skills/security.md)."""
import re
from pathlib import Path

SECRET = re.compile(r"AIza[0-9A-Za-z_-]{30,}|sk-or-[0-9A-Za-z-]{20,}|sk-[A-Za-z0-9]{32,}|gsk_[0-9A-Za-z]{20,}|"
                    r"hf_[0-9A-Za-z]{20,}|nvapi-[0-9A-Za-z_-]{20,}|ghp_[0-9A-Za-z]{30,}|github_pat_\w{30,}|"
                    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|service_role")
INSECURE = re.compile(r"""(?:src|href|action)\s*=\s*["']http://(?!localhost|127\.0\.0\.1)""", re.I)
BLANK = re.compile(r"<a\b(?=[^>]*target\s*=\s*[\"']_blank)(?![^>]*\brel\s*=)([^>]*)>", re.I)
SCRIPT = re.compile(r"""<script\b[^>]*\bsrc\s*=\s*["']https?://([^/"']+)""", re.I)
TRUSTED = ("cdnjs.cloudflare.com", "cdn.jsdelivr.net", "unpkg.com", "www.gstatic.com", "code.jquery.com",
           "cdn.tailwindcss.com")


def check(text: str) -> tuple[str, list[str]]:
    """Return the text with safe fixes applied, and the problems a person has to look at."""
    text = BLANK.sub(lambda m: f'<a{m.group(1)} rel="noopener noreferrer">', text)  # new-tab links can't control this page
    problems = []
    if SECRET.search(text):
        problems.append("HIGH: an API key or secret is inside the site; remove it and rotate the key")
    if INSECURE.search(text):
        problems.append("MEDIUM: a link or file uses http:// instead of https://")
    for host in sorted({h.lower() for h in SCRIPT.findall(text)} - set(TRUSTED)):
        problems.append(f"MEDIUM: a script loads from an unknown host ({host})")
    return text, problems


def scan_site(folder: Path) -> list[str]:
    """Check and fix every HTML/JS file of a built site in place."""
    problems = []
    for f in sorted(folder.rglob("*")):
        if f.suffix not in (".html", ".js") or not f.is_file():
            continue
        old = f.read_text(encoding="utf-8", errors="ignore")
        new, found = check(old)
        if new != old:
            f.write_text(new, encoding="utf-8")
        problems += [f"{p} ({f.relative_to(folder).as_posix()})" for p in found]
    return problems
