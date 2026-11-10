"""The owner's taste: every 👍/👎 he gives a design or video, and the designs he approved.

Agents read this before designing; Mostafa checks new work against it. Stays on this laptop (git-ignored).
"""
import shutil
from datetime import datetime
from pathlib import Path

from .config import ROOT

KNOW = ROOT / "knowledge"
TASTE = KNOW / "taste.md"
FEEDBACK = KNOW / "feedback.md"
APPROVED = KNOW / "examples" / "approved"
BRAND = KNOW / "brand"
SKILL_DIR = KNOW / "skills"
SKILLS = {  # who reads which playbook in knowledge/skills/ ("quality" is everyone's)
    "layla": ["quality"],
    "karim": ["quality", "design", "site-functionality", "copywriting", "quality-gate", "security"],
    # the API art director of the site factory: briefs the local model, then fixes its work
    "director": ["quality", "design", "copywriting", "arabic-dialect", "factory-brief", "factory-review", "factory-pieces"],
    "mostafa": ["quality", "design", "quality-gate", "security"],
    "tarek": ["quality", "quality-gate", "security"],
    "youssef": ["quality", "copywriting"],
    "omar": ["quality", "client-proposal"],
    "ziad": ["quality", "client-messages"],
    "adam": ["quality", "social-content"],
    "hassan": ["quality", "social-content", "image-prompts"],
}


def playbook() -> str:
    """What to do when… (clients, prices, tech problems, marketing): Layla answers the owner's questions from it."""
    return (KNOW / "playbook.md").read_text(encoding="utf-8")


def skills(key: str) -> str:
    """The teammate's skill playbooks, ready to append to his instructions ('' if he has none)."""
    texts = [(SKILL_DIR / f"{n}.md").read_text(encoding="utf-8") for n in SKILLS.get(key, [])]
    if not texts:
        return ""
    return "\n\nYOUR SKILLS (the owner's taste file wins if they disagree):\n\n" + "\n\n".join(texts)


def add_feedback(kind: str, vote: str, comment: str, title: str, files: list[Path]) -> Path | None:
    """Save one verdict. 👍 also keeps a copy of the work as an approved example. Returns the example folder."""
    FEEDBACK.parent.mkdir(parents=True, exist_ok=True)
    if not FEEDBACK.exists():
        FEEDBACK.write_text("# What the owner liked and disliked\n\nNewest last. Follow the likes, avoid the dislikes.\n", encoding="utf-8")
    good = vote == "up"
    line = f"\n## {datetime.now():%Y-%m-%d %H:%M} · {kind} · {title} · {'👍 liked' if good else '👎 disliked'}\n{comment.strip() or '(no comment)'}\n"
    with open(FEEDBACK, "a", encoding="utf-8") as f:
        f.write(line)
    if not good:
        return None
    dest = APPROVED / f"{datetime.now():%Y-%m-%d}_{kind}_{_safe(title)}"
    dest.mkdir(parents=True, exist_ok=True)
    for src in files:
        if src.is_file():
            shutil.copy2(src, dest / src.name)
    (dest / "why.md").write_text(f"# {title}\n\n{comment.strip() or 'Approved without a comment.'}\n", encoding="utf-8")
    return dest


def taste(kind: str = "", limit: int = 4000) -> str:
    """The owner's taste file, his saved feedback and his approved examples, ready to paste into an agent's instructions."""
    parts = []
    if TASTE.exists():  # written up front, so the team knows his taste before the first 👍/👎
        parts.append(TASTE.read_text(encoding="utf-8"))
    if FEEDBACK.exists():
        text = FEEDBACK.read_text(encoding="utf-8")
        parts.append("THE OWNER'S TASTE (his own 👍/👎 notes, newest last; follow them):\n" + text[-limit:])
    examples = sorted(APPROVED.glob(f"*_{kind}_*" if kind else "*"))[-3:] if APPROVED.exists() else []
    for ex in examples:
        why = (ex / "why.md").read_text(encoding="utf-8") if (ex / "why.md").exists() else ""
        sample = next((p for p in ex.iterdir() if p.suffix in (".json", ".md") and p.name != "why.md"), None)
        body = sample.read_text(encoding="utf-8")[:2500] if sample else ""
        parts.append(f"APPROVED EXAMPLE ({ex.name}): {why.strip()}\n{body}")
    return "\n\n".join(parts)


def _safe(s: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in s)[:40].strip("-") or "work"
