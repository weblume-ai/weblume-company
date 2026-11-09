"""Things the owner asks for in the chat that run on his laptop: create a GitHub repo, run a safe command.

Security, by design:
- Nothing runs without the owner pressing "نفّذ" in the dashboard first (Run.ask).
- Only programs on ALLOWED run, never through a shell, so `&`, `|`, `;`, `>` can't chain or redirect anything.
- python/node may only run a .py/.js file, never code typed into the command.
- Commands run inside WORKSPACE only; a path argument or folder outside it is refused.
- API keys and tokens are removed from the environment the command sees; output is cut short.
- GitHub organizations can't be created by API (GitHub's rule), so the owner gets the link instead.
"""
import os
import re
import shlex
import subprocess
from pathlib import Path

from . import publish

WORKSPACE = Path(os.getenv("WEBLUME_WORKSPACE", str(Path.home() / "Downloads" / "Projects"))).resolve()
ALLOWED = {  # program -> allowed first arguments (None = a .py/.js file)
    "git": {"status", "log", "diff", "init", "add", "commit", "push", "pull", "clone", "branch", "checkout", "remote", "fetch"},
    "npm": {"install", "ci", "run", "test", "init"},
    "node": None,
    "python": None,
}
BLOCKED = re.compile(r"[&|;<>`$%^]|\.\.[\\/]|\b(rm|del|rmdir|format|shutdown|reg|powershell|pwsh|cmd|curl|wget|certutil|bitsadmin)\b", re.I)
SECRET_ENV = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|PASS|HF_|PAT\b", re.I)
DO = re.compile(r"اعمل|اعملي|[أا]نش[ئي]|create|make|new|جديد", re.I)
REPO = re.compile(r"\b(?:repo|repository)\b|ريب(?:و|وزيتوري)?", re.I)
ORG = re.compile(r"\b(?:org|organi[sz]ation)\b|[أا]ورج[ا]?ن[يى]?ز[يى]?شن|[أا]رجان[يى]?زيشن", re.I)
RUN = re.compile(r"^\s*(?:شغ[ّ]?ل|نف[ّ]?ذ|run)\s+(?:(?:في|in)\s+([\w.-]+)\s*[:：]\s*)?(.+)$", re.I | re.S)
STOP = {"repo", "repository", "create", "make", "new", "private", "public", "in", "org", "github", "named", "called", "name"}


def intent(text: str) -> dict | None:
    """What the owner asked for, or None if it's a normal message for the team."""
    m = RUN.match(text)
    if m:
        return {"kind": "command", "folder": m.group(1) or "", "command": m.group(2).strip().strip("`")}
    if ORG.search(text) and DO.search(text) and not REPO.search(text.replace("ريبورت", "")):
        return {"kind": "org"}
    if REPO.search(text) and DO.search(text):
        own = re.search(r"(?:في|in|at|على|جوه)\s+([A-Za-z0-9][A-Za-z0-9-]{0,38})", text)
        named = re.search(r"(?:اسمه|اسمها|باسم|بإسم|named|called|name)\s+([A-Za-z0-9][A-Za-z0-9._-]{0,99})", text, re.I)
        words = [w for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", text)
                 if w.lower() not in STOP and not (own and w == own.group(1))]
        name = named.group(1) if named else (words[0] if words else "")
        return {"kind": "repo", "name": publish.repo_name(name), "owner": own.group(1) if own else "",
                "private": bool(re.search(r"private|برايفت|خاص|سري", text, re.I))}
    return None


def check_command(command: str) -> list[str]:
    """Split the command and make sure it's allowed; raise ValueError with the reason if not."""
    if BLOCKED.search(command):
        raise ValueError("الأمر ده فيه حاجة ممنوعة (ربط أوامر، حذف، أو برنامج خطر). مش هنفذه.")
    try:
        args = [a.strip("\"'") for a in shlex.split(command, posix=False)]
    except ValueError:
        raise ValueError("مش فاهم الأمر، اكتبه تاني.") from None
    if not args:
        raise ValueError("الأمر فاضي.")
    prog = args[0].lower().removesuffix(".exe").removesuffix(".cmd")
    if prog not in ALLOWED:
        raise ValueError(f"مسموح بس: {', '.join(ALLOWED)}.")
    subs = ALLOWED[prog]
    if subs is not None and (len(args) < 2 or args[1].lower() not in subs):
        raise ValueError(f"مع {prog} مسموح بس: {', '.join(sorted(subs))}.")
    if subs is None and (len(args) < 2 or args[1].startswith("-") or not args[1].lower().endswith((".py", ".js"))):
        raise ValueError(f"مع {prog} مسموح بس تشغيل ملف .py أو .js جوه فولدر الشغل، مش كود مكتوب في الأمر.")
    for a in args[1:]:  # an absolute path must stay inside the workspace
        if re.match(r"^[A-Za-z]:[\\/]|^[\\/]", a) and not _inside(Path(a)):
            raise ValueError(f"المسار ده برا فولدر الشغل ({WORKSPACE}).")
    return [prog, *args[1:]]


def _inside(path: Path) -> bool:
    p = path.resolve()
    return p == WORKSPACE or WORKSPACE in p.parents


def folder(name: str) -> Path:
    """The folder a command runs in: the workspace, or one folder inside it."""
    cwd = (WORKSPACE / name).resolve() if name else WORKSPACE
    if not cwd.is_dir() or not _inside(cwd):
        raise ValueError(f"مفيش فولدر اسمه {name} جوه {WORKSPACE}.")
    return cwd


def run_command(args: list[str], cwd: Path = WORKSPACE) -> str:
    """Run an already-checked command with no shell, no secrets in its environment, 5 minutes max."""
    env = {k: v for k, v in os.environ.items() if not SECRET_ENV.search(k)}
    exe = {"python": str(Path(__file__).resolve().parents[1] / ".venv" / "Scripts" / "python.exe")}.get(args[0], args[0])
    try:
        r = subprocess.run([exe, *args[1:]], cwd=cwd, env=env, capture_output=True, text=True, timeout=300,
                           shell=False, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return f"✕ {args[0]} مش متسطب على الجهاز."
    except subprocess.TimeoutExpired:
        return "✕ الأمر خد أكتر من 5 دقايق ووقفته."
    out = (r.stdout + r.stderr).strip()
    return f"{'✓' if r.returncode == 0 else f'✕ (كود {r.returncode})'} {out[-700:] or 'خلص من غير رسالة'}"


def create_repo(name: str, private: bool, owner: str = "") -> str:
    """Create a GitHub repo (with a README) using the owner's sign-in on this laptop. Returns its URL."""
    token = publish._token()
    code, me = publish._call("GET", "/user", token)
    if code != 200:
        raise RuntimeError("GitHub مش قابل تسجيل الدخول اللي على الجهاز. سجل دخول تاني بـ git.")
    owner = owner or me["login"]
    where = "/user/repos" if owner.lower() == me["login"].lower() else f"/orgs/{owner}/repos"
    code, res = publish._call("POST", where, token, {"name": name, "private": private, "auto_init": True})
    if code == 422:
        raise ValueError(f"فيه ريبو اسمه {name} في {owner} أصلاً.")
    if code != 201:
        raise RuntimeError(f"GitHub رفض: {res.get('message', code)}")
    return res["html_url"]


def handle(run, text: str):
    """Do what the owner asked, after he approves it in the chat."""
    it = intent(text) or {}
    if it.get("kind") == "org":
        run.say("layla", "you", "GitHub مش بيسمح لأي برنامج يعمل Organization. اعملها من هنا (دقيقة، Free): "
                                "https://github.com/account/organizations/new وقولي اسمها، وأنا أعمل فيها الريبوهات.", full=True)
        return
    if it.get("kind") == "repo":
        if not it["name"]:
            run.say("karim", "you", "محتاج اسم للريبو بالإنجليزي، مثلاً: اعمل ريبو cafe-site")
            return
        ans = run.ask("karim", f"أعمل ريبو {it['name']} ({'خاص' if it['private'] else 'عام'}) في {it['owner'] or 'حسابك'}؟", ["نفّذ", "لا"])
        if ans["choice"] != "نفّذ":
            run.say("karim", "you", "تمام، ماعملتش حاجة.")
            return
        run.set_agent("karim", "working")
        run.say("karim", "you", "اتعمل ✓ " + create_repo(it["name"], it["private"], it["owner"]), full=True)
        run.set_agent("karim", "done")
        return
    if it.get("kind") == "command":
        try:
            args, cwd = check_command(it["command"]), folder(it["folder"])
        except ValueError as e:
            run.say("karim", "you", str(e), full=True)
            return
        ans = run.ask("karim", f"أشغّل على جهازك؟\n{' '.join(args)}\n(في {cwd})", ["نفّذ", "لا"])
        if ans["choice"] != "نفّذ":
            run.say("karim", "you", "تمام، ماشغلتش حاجة.")
            return
        run.set_agent("karim", "working")
        run.say("karim", "you", run_command(args, cwd), full=True)
        run.set_agent("karim", "done")
