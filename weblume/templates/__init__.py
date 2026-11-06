"""Ready animated site templates for Karim, plus the motion kit injected into every site he builds."""
import re
from pathlib import Path

DIR = Path(__file__).parent
CSS_MARK, JS_MARK = "<!--WEBLUME:MOTION_CSS-->", "<!--WEBLUME:MOTION_JS-->"
KINDS = {  # template -> words that pick it (Arabic + English)
    "cafe": ["café", "cafe", "coffee", "restaurant", "bakery", "food", "kitchen", "pizza", "burger", "كافيه", "كافية",
             "قهوة", "مطعم", "مخبز", "حلويات", "أكل", "اكل", "كشري", "مشويات"],
    "clinic": ["clinic", "doctor", "dental", "dentist", "salon", "spa", "gym", "lawyer", "school", "center", "service",
               "عيادة", "دكتور", "أسنان", "اسنان", "صالون", "جيم", "محامي", "مدرسة", "مركز", "خدمات"],
    "shop": ["shop", "store", "boutique", "brand", "clothes", "gift", "perfume", "متجر", "محل", "براند", "هدايا",
             "ملابس", "عطور", "اكسسوارات"],
}


def pick(text: str) -> str:
    """Which template fits the request; cafés and restaurants are the default (Weblume's main clients)."""
    t = text.lower()
    scores = {k: sum(w in t for w in words) for k, words in KINDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "cafe"


def load(kind: str) -> str:
    return (DIR / f"{kind}.html").read_text(encoding="utf-8")


def guide() -> str:
    return (DIR / "GUIDE.md").read_text(encoding="utf-8")


_STOCK = re.compile(r'<img\b[^>]*\bsrc="https?://(?:[\w-]+\.)*(?:unsplash|pexels|pixabay|picsum|placehold|loremflickr)\.[^"]*"[^>]*>', re.I)


def strip_stock_photos(html: str) -> tuple[str, int]:
    """Stock photos make every site look the same: swap them for labeled placeholders for the client's real photos."""
    def ph(m):
        tag = m.group(0)
        alt = re.search(r'\balt="([^"]*)"', tag)
        cls = re.search(r'\bclass="([^"]*)"', tag)
        classes = " ".join(dict.fromkeys(["ph", *(cls.group(1).split() if cls else [])]))
        label = ((alt.group(1) + " · ") if alt and alt.group(1) else "") + "صورة حقيقية من العميل"
        return f'<div class="{classes}" data-label="{label}"></div>'
    html, n = _STOCK.subn(ph, html)
    html, m = re.subn(r'<meta\b[^>]*content="https?://(?:[\w-]+\.)*(?:unsplash|pexels|pixabay|picsum)\.[^"]*"[^>]*>\s*', "", html, flags=re.I)
    return html, n + m


def claims_to_check(html: str) -> list[str]:
    """Things that are often invented: the owner must confirm them with the client before the site goes out."""
    text = re.sub(r"<[^>]+>", " ", html)
    found = []
    if re.search(r"آراء|قالوا عن|testimonial|reviews?\b|what (our )?(customers|clients) say", text, re.I):
        found.append("a reviews section (keep only real reviews from the client)")
    if "data-count=" in html or re.search(r"\d(\.\d)?\s*★|★\s*\d", text):
        found.append("numbers / ratings (years, customers, Google rating)")
    return found


def inject_motion(html: str) -> str:
    """Put the motion kit into the page, at the markers if Karim kept them, else before </head> and </body>."""
    css = "<style>/* wl-motion-kit */\n" + (DIR / "motion.css").read_text(encoding="utf-8") + "</style>"
    js = "<script>\n" + (DIR / "motion.js").read_text(encoding="utf-8") + "</script>"
    if "/* wl-motion-kit */" in html:  # already injected (e.g. the draft went through twice)
        return html
    for mark, code, before in ((CSS_MARK, css, "</head>"), (JS_MARK, js, "</body>")):
        if mark in html:
            html = html.replace(mark, code, 1)
        elif before in html.lower():
            i = html.lower().rfind(before)
            html = html[:i] + code + "\n" + html[i:]
        else:
            html += code
    return html
