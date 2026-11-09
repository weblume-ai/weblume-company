"""A clean type logo (SVG) for a client who has none yet: the name set well, plus a simple mark from its initials.
Typography only, no drawings (the owner dislikes code-drawn visuals). The client should send a real logo later."""
import hashlib
from html import escape

FONT = "'Segoe UI','Tahoma','Arial',sans-serif"  # system fonts: an SVG used as an <img> can't load web fonts


GENERIC = {"مطعم", "كافيه", "كافية", "مقهى", "محل", "متجر", "عيادة", "cafe", "café", "restaurant", "the", "shop", "studio"}


def initials(name: str) -> str:
    """Up to two latin initials, or one Arabic letter (Arabic letters joined together read as a word, not initials)."""
    words = [w for w in name.replace("-", " ").split() if w[:1].isalnum() and w.lower() not in GENERIC] or name.split()[:1]
    if any("؀" <= c <= "ۿ" for c in "".join(words)):
        return words[0].removeprefix("ال")[:1] if words else "W"
    return "".join(w[0] for w in words[:2]).upper() or "W"


def make(name: str, color: str = "#141414", ink: str = "#141414") -> str:
    """One of three layouts, picked from the name so the same client always gets the same logo."""
    name = " ".join(name.split())[:28] or "Brand"
    style = int(hashlib.md5(name.encode()).hexdigest(), 16) % 3
    size, ini = 64, escape(initials(name))
    w = int(len(name) * size * .62) + 40
    text = f'font-family="{FONT}" font-weight="700"'
    if style == 0:  # rounded square with initials, name beside it
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w + 130} 120" role="img" aria-label="{escape(name)}">'
                f'<rect x="4" y="4" width="112" height="112" rx="28" fill="{color}"/>'
                f'<text x="60" y="78" text-anchor="middle" font-size="48" fill="#fff" {text}>{ini}</text>'
                f'<text x="136" y="82" font-size="{size}" fill="{ink}" {text} letter-spacing="-1">{escape(name)}</text></svg>')
    if style == 1:  # ring with the first letter, name beside it
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w + 130} 120" role="img" aria-label="{escape(name)}">'
                f'<circle cx="60" cy="60" r="50" fill="none" stroke="{color}" stroke-width="9"/>'
                f'<text x="60" y="78" text-anchor="middle" font-size="50" fill="{color}" {text}>{ini[:1]}</text>'
                f'<text x="136" y="82" font-size="{size}" fill="{ink}" {text} letter-spacing="-1">{escape(name)}</text></svg>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w + 30} 120" role="img" aria-label="{escape(name)}">'  # name + accent bar
            f'<text x="10" y="76" font-size="{size + 6}" fill="{ink}" {text} letter-spacing="-1.5">{escape(name)}</text>'
            f'<rect x="12" y="94" width="{min(w - 20, 120)}" height="10" rx="5" fill="{color}"/></svg>')
