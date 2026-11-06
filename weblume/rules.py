"""Business rules enforced in code, so they hold even when a model ignores its instructions."""
import json
import re
import unicodedata

from .config import CONTACTED_FILE, WEBSITE

# ---------- Sara: never a phone number in captions or scripts ----------
_PHONE = re.compile(r"(?:\+|00)?[\d٠-٩۰-۹](?:[\d٠-٩۰-۹\s\-.()]{6,})[\d٠-٩۰-۹]")
_WA_LINK = re.compile(r"(?:https?://)?(?:wa\.me|api\.whatsapp\.com|chat\.whatsapp\.com)/\S*", re.I)


def remove_phone_numbers(text: str) -> tuple[str, int]:
    """Replace phone numbers and WhatsApp links with the Weblume website. Returns (text, how many replaced)."""
    note = f"(تواصل معانا من موقع Weblume: {WEBSITE})"
    count = 0

    def repl(m):
        nonlocal count
        digits = sum(ch.isdigit() for ch in m.group(0))
        if digits < 8:  # years, prices, times: not a phone number
            return m.group(0)
        count += 1
        return note

    text = _PHONE.sub(repl, text)
    text, n = _WA_LINK.subn(note, text)
    return text, count + n


# ---------- Ziad: never message a business that was already contacted ----------
def normalize_name(name: str) -> str:
    # drop accents and Arabic tashkeel, so "Café" == "cafe" and "مَطعم" == "مطعم"
    s = "".join(ch for ch in unicodedata.normalize("NFKD", str(name)) if unicodedata.category(ch) != "Mn").lower()
    s = re.sub(r"[إأآا]", "ا", s).replace("ة", "ه").replace("ى", "ي")
    return re.sub(r"[\W_]+", "", s)


def load_contacted() -> list[dict]:
    if not CONTACTED_FILE.exists():
        return []
    try:
        data = json.loads(CONTACTED_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        # A broken file must not silently count as "nobody contacted"
        raise RuntimeError(f"{CONTACTED_FILE.name} is not valid JSON. Fix it before running Ziad.")


def is_contacted(name: str, contacted: list[dict]) -> bool:
    n = normalize_name(name)
    return bool(n) and any(normalize_name(c.get("business", "")) == n for c in contacted)


def mark_contacted(business: str, city: str = "", note: str = "") -> bool:
    """Add a business to contacted.json. Returns False if it was already there."""
    from datetime import datetime

    contacted = load_contacted()
    if is_contacted(business, contacted):
        return False
    contacted.append({"business": business.strip(), "city": city.strip(), "note": note.strip(),
                      "date": datetime.now().strftime("%Y-%m-%d")})
    CONTACTED_FILE.write_text(json.dumps(contacted, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def split_contacted(names: list[str], contacted: list[dict]) -> tuple[list[str], list[str]]:
    """(new names, already contacted names). Duplicates in the input are dropped."""
    new, old, seen = [], [], set()
    for name in names:
        name = name.strip()
        key = normalize_name(name)
        if not key or key in seen:
            continue
        seen.add(key)
        (old if is_contacted(name, contacted) else new).append(name)
    return new, old


# ---------- parsing model answers ----------
_JSON_LINE = re.compile(r'^(\s*"[^"]+"\s*:\s*")(.*)("\s*,?\s*)$')


def _escape_inner_quotes(text: str) -> str:
    """Models often write  "message": "قال "أهلا" ليهم",  -> escape the quotes inside the value."""
    def fix(line):
        m = _JSON_LINE.match(line)
        return m.group(1) + re.sub(r'(?<!\\)"', r'\\"', m.group(2)) + m.group(3) if m else line
    return "\n".join(fix(l) for l in text.splitlines())


def extract_json(text: str):
    """First JSON object or array in a model answer (models like wrapping it in ``` fences)."""
    text = re.sub(r"```(?:json)?", "", str(text))
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end > start:
            for candidate in (text[start:end + 1], _escape_inner_quotes(text[start:end + 1])):
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
    return None


def extract_html(text: str) -> str:
    """The HTML document inside a model answer, without ``` fences or chat around it."""
    text = str(text)
    fenced = re.search(r"```(?:html)?\s*(.*?)```", text, re.S | re.I)
    if fenced and "<html" in fenced.group(1).lower():
        text = fenced.group(1)
    low = text.lower()
    start = low.find("<!doctype")
    if start == -1:
        start = low.find("<html")
    end = low.rfind("</html>")
    if start != -1 and end != -1:
        return text[start:end + len("</html>")].strip()
    return text.strip()


def slug(name: str, fallback: str = "client") -> str:
    s = re.sub(r"[^\w\-]+", "-", str(name).strip(), flags=re.U).strip("-_").lower()
    return s[:60] or fallback
