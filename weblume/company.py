"""Runs the company: plans the work, runs the agents in order, saves every output and a live status file."""
import json
import os
import re
import subprocess
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

from crewai import Crew, Process, Task

from . import config, inspiration, knowledge, logo, ops, publish as publisher, rules, security, templates, tester, video
from .config import CURRENCY, MAX_RPM, OUTPUT_DIR, PROVIDER, RUNS_DIR, WEBSITE, get_llm, model_name
from .team import ORDER, TEAM, make_agent

_lock = threading.Lock()
_active: dict = {"thread": None, "run": None}
JOB = {"karim": "code", "mostafa": "code", "layla": "fast"}  # with LLM_PROVIDER=auto; everyone else writes ("write")
TEST_ROUNDS = 2  # Tarek tests, Karim fixes what he found, Tarek tests once more


def short(text: str, n: int = 170) -> str:
    """One chat line: whitespace collapsed, cut at the last sentence end before n characters."""
    t = " ".join(text.split())
    if len(t) <= n:
        return t
    cut = max(t.rfind(s, 0, n) for s in (". ", "، ", "؛ ", "! ", "؟ ", " → "))
    return (t[:cut + 1] if cut > n // 2 else t[:n].rsplit(" ", 1)[0]) + " …"


# ---------------------------------------------------------------- run record
class Run:
    """One job. Everything the dashboard shows comes from status.json in the run folder."""

    def __init__(self, goal: str, mode: str, client: str, names: list[str]):
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.dir = RUNS_DIR / f"{stamp}_{rules.slug(goal[:40], 'task')}"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.status = {
            "id": self.dir.name, "goal": goal, "mode": mode, "client": client, "names": names,
            "llm": f"{PROVIDER} / {model_name()}", "state": "running", "error": "",
            "started": datetime.now().isoformat(timespec="seconds"), "finished": "",
            "agents": {k: {"status": "idle", "output": ""} for k in ["layla", *ORDER]},
            "tasks": [], "files": [], "leads": None, "chat": [], "test": None, "site": "",
            "ask": None, "video": "", "feedback": {},
        }
        self.current = "layla"
        self.kind, self.site_dir, self.site_text = "", None, ""
        self.steps, self.inbox, self.answers, self.cond = [], [], {}, threading.Condition()
        self.lock = threading.RLock()  # Layla may answer the owner while the team works: one writer at a time
        self.save()

    def save(self):
        with self.lock:
            self._save()

    def _save(self):
        tmp = self.dir / "status.tmp"
        tmp.write_text(json.dumps(self.status, ensure_ascii=False, indent=1), encoding="utf-8")
        for _ in range(20):  # the dashboard may be reading the file this instant (Windows locks it)
            try:
                os.replace(tmp, self.dir / "status.json")
                return
            except PermissionError:
                time.sleep(0.05)

    def log(self, who: str, text: str):
        line = f"{datetime.now():%H:%M:%S} [{TEAM[who]['name'] if who in TEAM else who}] {text}\n"
        with open(self.dir / "run.log", "a", encoding="utf-8") as f:
            f.write(line)

    def say(self, frm: str, to: str, text: str, full: bool = False):
        """One teammate talks to another: shown as a chat line and a speech bubble in the 3D office.
        Teammates keep it short (details are in the files); the owner's words, questions and results stay whole."""
        if not full and frm != "you":
            text = short(text)
        with self.lock:
            self.status["chat"].append({"t": datetime.now().isoformat(timespec="seconds"), "from": frm, "to": to, "text": text})
            self.log(frm, f"→ {TEAM.get(to, {}).get('name', to)}: {text}")
            self.save()

    def update(self, key: str, text: str):
        """A teammate tells the owner what they're doing, finished, or doing next."""
        self.say(key, "you", text)

    def ask(self, key: str, question: str, options: list[str]) -> dict:
        """Pause this teammate until the owner answers in the dashboard. Returns {"choice", "text"}."""
        with self.cond:
            qid = len(self.status["chat"])
            prev = self.status["agents"][key]["status"]
            self.status["ask"] = {"id": qid, "agent": key, "question": question, "options": options}
            self.status["agents"][key]["status"] = "asking"
            self.say(key, "you", question, full=True)
            while qid not in self.answers:
                self.cond.wait(timeout=1)
            ans = self.answers.pop(qid)
            self.status["ask"] = None
            self.status["agents"][key]["status"] = prev
        self.say("you", key, ans["choice"] + (f" — {ans['text']}" if ans["text"] else ""))
        return ans

    def answer(self, qid: int, choice: str, text: str):
        with self.cond:
            ask = self.status.get("ask")
            if not ask or ask["id"] != qid:
                raise ValueError("This question was already answered.")
            if choice not in ask["options"] and not text.strip():
                raise ValueError("Pick one of the options or write your answer.")
            self.answers[qid] = {"choice": choice if choice in ask["options"] else "رد مكتوب", "text": text.strip()}
            self.cond.notify_all()

    def set_agent(self, key: str, status: str, output: str | None = None):
        self.status["agents"][key]["status"] = status
        if output is not None:
            self.status["agents"][key]["output"] = output
        self.save()

    def add_file(self, path: Path):
        self.status["files"].append(str(path.relative_to(OUTPUT_DIR)))

    def write(self, name: str, text: str) -> Path:
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        self.add_file(path)
        self.save()
        return path


# ---------------------------------------------------------------- planning
PLAN_HINT = {
    "omar": "client brief -> project spec and price",
    "youssef": "website copy in Egyptian Arabic + English",
    "karim": "builds the website from Weblume's premium templates",
    "mostafa": "reviews the site's code and content, sends fixes to Karim",
    "tarek": "tests the finished site in a real browser and judges if it's good enough",
    "ziad": "lead finding and outreach messages",
    "adam": "TikTok / Instagram ideas, scripts, captions",
    "hassan": "turns Adam's script into a vertical video (MP4)",
}
WEBSITE_TEAM = ["omar", "youssef", "karim", "mostafa", "tarek"]


def plan_task(goal: str, agent) -> Task:
    team = "\n".join(f"- {k}: {TEAM[k]['name']} ({v})" for k, v in PLAN_HINT.items())
    return Task(
        description=(
            f"The owner of Weblume asked:\n\"\"\"{goal}\"\"\"\n\n"
            f"Your team:\n{team}\n\n"
            "Decide who is needed. A new website normally needs omar, youssef, karim, mostafa and tarek. "
            "Pick only who the request really needs.\n"
            "Also pull out the client/business name if the request is about one client's website, and any "
            "real business names the owner listed for outreach.\n"
            "Answer with JSON only, no other text, exactly in this shape:\n"
            '{"agents": [<the keys you chose>], "client_name": "", "business_names": [], "reason": "one sentence"}'
        ),
        expected_output="A JSON object with agents, client_name, business_names and reason.",
        agent=agent,
    )


def wants_website(goal: str) -> bool:
    g = goal.lower()
    return any(w in g for w in ["build a site", "website", "landing page", "اعمل موقع", "موقع ل", "صفحة هبوط"])


def keyword_plan(goal: str) -> list[str]:
    """Fallback when Layla's answer is not valid JSON."""
    g = goal.lower()
    picks = []
    if any(w in g for w in ["lead", "outreach", "عملاء", "رسايل", "رسائل", "تواصل مع"]):
        picks.append("ziad")
    if any(w in g for w in ["tiktok", "instagram", "reel", "تيك", "انستا", "فيديو", "caption", "كابشن", "video"]):
        picks.append("adam")
    if any(w in g for w in ["فيديو", "video", "reel", "ريل"]):
        picks.append("hassan")
    if not picks or wants_website(goal):
        picks = [*WEBSITE_TEAM, *picks]
    return picks


def parse_plan(text: str, goal: str) -> dict:
    data = rules.extract_json(text)
    if not isinstance(data, dict):
        data = {}
    chosen = data.get("agents") if isinstance(data.get("agents"), list) else []
    agents = [a for a in ORDER if a in [str(x).lower().strip() for x in chosen]]
    if agents and wants_website(goal) and "karim" not in agents:  # small models sometimes stop at the spec
        agents = [a for a in ORDER if a in agents or a in WEBSITE_TEAM]
    names = data.get("business_names") if isinstance(data.get("business_names"), list) else []
    return {
        "agents": agents or keyword_plan(goal),
        "client_name": str(data.get("client_name") or "").strip(),
        "business_names": [str(n) for n in names if str(n).strip()],
        "reason": str(data.get("reason") or ("keyword fallback" if not agents else "")),
    }


# ---------------------------------------------------------------- work tasks
NO_FAKES = ("NEVER invent reviews, testimonials, ratings, years, customer counts, awards or prices: use only what "
            "the request or spec gives.")


NAME_AND_LOGO = ("If the request gives no business name, choose a short, memorable name that fits the business and the "
                 "client's language and use it everywhere (never leave a placeholder name). If the client sent no logo, "
                 "use logo.svg: the code makes a clean type logo from the name and the --accent color.")


def karim_brief(kind: str, goal: str = "") -> str:
    """What Karim is told to produce for this template, starting with the owner's saved taste."""
    ideas = ("\n\nDESIGN IDEAS FOR THIS SITE (adapt them to this business and its real photos; never copy a site):\n"
             + inspiration.brief(goal, kind)) if kind == "fresh" and goal else ""
    return (knowledge.taste("site") + "\n\n" if knowledge.taste("site") else "") + _karim_brief(kind) + "\n\n" + NAME_AND_LOGO + ideas


def _karim_brief(kind: str) -> str:
    if kind in templates.FOLDER:
        return ("The design, scroll scenes and animations of this template are finished and approved. You write ONLY "
                "the client's content as ONE JSON object in exactly the shape of the example below, following the "
                f"guide. {NO_FAKES}\n\nGUIDE:\n{templates.guide(kind)}\n\nEXAMPLE (another café's content: copy the "
                f"shape, not the words):\n{templates.load(kind)}\n\nOutput ONLY the JSON object, nothing before or after.")
    return ("Build the website by EDITING the ready Weblume template below. Fill it with the real content from the "
            "spec and copy (Arabic in the markup, English in data-en), set the client's brand colors in the :root "
            "variables, keep the sections the client needs, remove the rest, and put the client's WhatsApp number in "
            "<body data-wa>. Keep it one file, mobile-first, with <title>, meta description and Open Graph filled in. "
            f"{NO_FAKES} Photos: real photo URLs from the request, free stock (Pexels) you are sure exists, or keep "
            f"the .ph placeholders.\n\nHOW THE ANIMATIONS WORK:\n{templates.guide()}\n\nTHE TEMPLATE ({kind}):\n"
            f"{templates.load(kind)}\n\nOutput ONLY the full edited HTML document from <!DOCTYPE html> to </html>.")


def build_tasks(keys: list[str], goal: str, client: str, names: list[str], agents: dict, run: Run) -> list[tuple]:
    """Tasks for the chosen agents, always in company order. Each entry: (Task, agent key, output file)."""
    t: dict[str, Task] = {}
    steps: list[tuple[Task, str, str]] = []
    run.kind = templates.pick(f"{goal} {client}")
    if "karim" in keys:  # the owner chooses the template
        labels = {"cafe": "كافيه (تصميم Loopie)", "fresh": "تصميم جديد مختلف (مكتبة الإلهام)", "clinic": "عيادة/خدمات",
                  "shop": "متجر", "game": "موقع لعبة (فيه لعبة شغالة)"}
        ans = run.ask("karim", "هعمل الموقع على أي قالب؟ الأول هو اقتراحي.", [labels[run.kind], *[v for k, v in labels.items() if k != run.kind]])
        run.kind = next((k for k, v in labels.items() if v == ans["choice"]), run.kind)
        if ans["text"]:
            goal += f"\nThe owner's note on the design: {ans['text']}"
    run.site_dir = OUTPUT_DIR / rules.slug(client or goal[:30])
    ext = ".json" if run.kind in templates.FOLDER else ".html"

    def add(name, key, file, description, expected, context):
        task = Task(description=description, expected_output=expected, agent=agents[key],
                    context=[c for c in context if c is not None])
        t[name] = task
        steps.append((task, key, file))

    if "omar" in keys:
        add("spec", "omar", "spec.md",
            f"Request from the owner:\n\"\"\"{goal}\"\"\"\nClient: {client or 'see request'}\n\n"
            "Write the project spec in Markdown with these headings: Client summary, Goal of the site, "
            "Pages (and the sections on each page), Features (e.g. menu, WhatsApp order button, map, booking, "
            "gallery, Arabic/English switch), Style direction (mood, brand colors, fonts, photos to use), "
            f"Suggested price range in {CURRENCY} (basic and with extras, with a one-line reason), "
            "Questions to ask the client. Do not invent facts about the client; mark unknowns as TODO.",
            "A Markdown project spec with all the headings above.", [])
    if "youssef" in keys:
        add("copy", "youssef", "content.md",
            f"Request:\n\"\"\"{goal}\"\"\"\n\nWrite the website copy for every page and section in the spec "
            "(or in the request if there is no spec). For each section give: Arabic (Egyptian dialect) and "
            "English. Include page titles, meta descriptions (under 155 characters), headlines (short, 6 words max), "
            "short body text and button labels. No fake reviews, numbers or awards.",
            "Markdown copy, section by section, Arabic then English.", [t.get("spec")])
    if "karim" in keys:
        run.log("karim", f"Template: {run.kind}")
        add("build", "karim", ("website_draft" if "mostafa" in keys else "website") + ext,
            f"Request:\n\"\"\"{goal}\"\"\"\n\n{karim_brief(run.kind, goal)}",
            "The client's site content." if ext == ".json" else "One complete HTML document.",
            [t.get("spec"), t.get("copy")])
    if "mostafa" in keys:
        add("review", "mostafa", "review.md",
            f"Request:\n\"\"\"{goal}\"\"\"\n\nReview Karim's work. "
            + ("It is the site's content as JSON for a finished Weblume template: check every field the guide asks "
               "for is there and correct, valid JSON shape, natural Egyptian Arabic and clean English, the "
               "translations match, images come only from the allowed list, brand colors are set, nothing is "
               "invented (prices, ratings, reviews). " if ext == ".json" else
               "Check: bugs in HTML/CSS/JS, layout on a 375px phone, RTL issues, spelling in Arabic and English, SEO "
               "basics (title, meta description, one h1, alt text, Open Graph), and that the copy matches the spec. "
               "The animations come from the motion kit injected at the <!--WEBLUME:...--> markers: keep the markers. ")
            + ("Also check the work against the owner's saved taste below and report anything that goes against it.\n"
               + knowledge.taste("site") + "\n" if knowledge.taste("site") else "")
            + "List every problem as: where -> what is wrong -> exact fix. End with a verdict line: READY or NEEDS FIXES.",
            "A Markdown review: a numbered list of problems with exact fixes, then the verdict.",
            [t.get("build"), t.get("copy"), t.get("spec")])
    if "karim" in keys and "mostafa" in keys:
        add("fix", "karim", "website" + ext,
            "Mostafa reviewed your work. Apply every fix from his review and return the whole corrected "
            + ("JSON object only." if ext == ".json" else
               "file. Keep the <!--WEBLUME:MOTION_CSS--> and <!--WEBLUME:MOTION_JS--> markers. Output ONLY the full "
               "HTML document from <!DOCTYPE html> to </html>."),
            "The corrected site content." if ext == ".json" else "One complete, corrected HTML document.",
            [t["build"], t["review"]])
    if "ziad" in keys:
        contacted = rules.load_contacted()
        new, old = rules.split_contacted(names, contacted)
        run.status["leads"] = {"skipped_contacted": old, "leads": [], "targets": []}
        run.save()
        if old:
            run.log("ziad", f"Already contacted, NOT drafting: {', '.join(old)}")
        if new:
            who = "Write one personal message for EACH of these businesses (and only these):\n" + \
                  "\n".join(f"- {n}" for n in new)
        elif names:
            who = "Every business the owner listed was already contacted, so write NO personal messages; " \
                  "leave \"leads\" empty and only fill \"targets\"."
        else:
            who = "The owner gave no business names, so write no personal messages: for each target kind give " \
                  "one message template with [اسم المكان] where the business name goes."
        add("leads", "ziad", "leads.md",
            f"Request:\n\"\"\"{goal}\"\"\"\n\nFrom the request, take the city/area and business type. List the "
            "kinds of businesses there that most need a website and why (e.g. cafés with good Google reviews "
            f"but no site). {who}\nMessages: Egyptian Arabic, 3-5 short lines, personal, mention the free "
            "domain and that they see the design before paying, end with one simple question. No phone numbers.\n"
            "Inside the text never use the \" character; for quotes use « ».\n"
            "Answer with JSON only:\n"
            '{"targets": [{"kind": "", "why": "", "template": ""}], '
            '"leads": [{"business": "", "message": ""}]}',
            "A JSON object with targets and leads.", [])
    if "adam" in keys:
        add("social", "adam", "social.md",
            f"Request:\n\"\"\"{goal}\"\"\"\n\nPlan TikTok / Instagram content for Weblume (black, red and white "
            "brand). For each video idea: title, hook (first 2 seconds), full short script with shots, on-screen "
            "text, caption in Egyptian Arabic, and hashtags. The call to action always sends people to the "
            f"Weblume website ({WEBSITE}). NEVER write a phone number or WhatsApp number anywhere.",
            "Markdown: numbered video ideas, each with hook, script, on-screen text, caption and hashtags.", [])
    if "hassan" in keys:
        sites = video.built_sites()
        add("video", "hassan", "video.json",
            f"Request:\n\"\"\"{goal}\"\"\"\n\n{knowledge.taste('video')}\n\nTurn the FIRST video idea in Adam's script into "
            "a vertical 9:16 Weblume video (black, red and white). Write it as scenes, 15–35 seconds in total. Scene types: "
            '"hook" (the first 2 seconds, max 7 words), "text" (one short line, optional "sub"), "site" (one of our websites '
            'scrolling inside a phone or laptop: "site" must be one of ' + json.dumps(sites, ensure_ascii=False) +
            ', "device": "phone" or "laptop", optional "caption"), "image" (a free AI photo: "prompt" in English describing a '
            'realistic photo with no text and no faces, plus a short Arabic "caption"). Each scene has "dur" in seconds '
            '(2–5). Egyptian Arabic. Use at most 2 image scenes. '
            "The code adds the closing 'contact us through the Weblume website' scene. NEVER write a phone number.\n"
            'Answer with JSON only: {"title": "", "scenes": [{"type": "hook", "text": "", "dur": 2.5}]}',
            "A JSON object with title and scenes.", [t.get("social")])
    return steps


# ---------------------------------------------------------------- after each task
def _site_name(html: str) -> str:
    """The business name from the page title ("Name | tagline")."""
    m = re.search(r"<title>\s*([^<|·—-]+)", html)
    return m.group(1).strip() if m else ""


def save_site(run: Run, key: str, file: str, raw: str, name: str) -> str:
    """Karim's output: a draft is kept in the run folder; the final one becomes the site in output/<client>/."""
    final = file.startswith("website.")
    if run.kind in templates.FOLDER:
        data = rules.extract_json(raw)
        if not isinstance(data, dict):
            run.log(key, "ERROR: the site content was not valid JSON; nothing was built.")
            run.write(name.replace(".json", "_invalid.txt"), raw)
            return "The site content was not valid JSON."
        text = json.dumps(data, ensure_ascii=False, indent=1)
        run.write(name, text)
        if final:
            made_up = templates.drop_unsourced(data, f"{run.status['goal']} {run.status['client']}")
            if made_up:
                run.log(key, f"RULE: removed {made_up.count('price')} price(s){' and the opening hours' if 'hours' in made_up else ''} "
                             "that weren't in your request (add the real ones to the request).")
            fixed = templates.build_site(run.kind, data, run.site_dir)
            if fixed:
                run.log(key, f"RULE: {fixed} image path(s) didn't exist, replaced with template photos.")
    else:
        text, dead = templates.fix_broken_images(rules.extract_html(raw))
        text = templates.inject_motion(text)
        if dead:
            run.log(key, f"RULE: {dead} photo link(s) didn't load, replaced with placeholders for real photos.")
        run.write(name, text)
        if final:
            run.site_dir.mkdir(parents=True, exist_ok=True)
            (run.site_dir / "index.html").write_text(text, encoding="utf-8")
            if "logo.svg" in text and not (run.site_dir / "logo.svg").exists():  # no client logo: a type logo from the name
                color = lambda v, d: (re.search(rf"{v}\s*:\s*(#[0-9a-fA-F]{{3,8}})", text) or [None, d])[1]
                (run.site_dir / "logo.svg").write_text(logo.make(_site_name(text), color("--accent", "#141414"), color("--ink", "#141414")), encoding="utf-8")
                run.update(key, f"عملت لوجو مؤقت بالاسم «{_site_name(text)}». ابعتلي اللوجو الحقيقي لو موجود.")
    if final:
        if not run.status["client"]:  # Karim named the business himself: tell the owner
            name = (data.get("name") if run.kind in templates.FOLDER else _site_name(text)) or ""
            if name:
                run.status["client"] = name
                run.update(key, f"مفيش اسم في الطلب، فاخترت «{name}». لو عايز اسم تاني قولي.")
        run.site_text = text
        site = run.site_dir / "index.html"
        run.status["site"] = str(site.relative_to(OUTPUT_DIR))
        run.add_file(site)
        run.log(key, f"Website saved to output/{run.site_dir.relative_to(OUTPUT_DIR).as_posix()}/")
        for claim in templates.claims_to_check(text):
            run.log(key, f"CHECK before sending: {claim}.")
        for problem in security.scan_site(run.site_dir):
            run.log(key, f"SECURITY: {problem}.")
        run.save()
    return text


def price_section(spec: str) -> list[str]:
    """Omar's suggested project price: the lines under his price heading (not the menu prices)."""
    m = re.search(r"^#+[^\n]*(price range|السعر|سعر المشروع|التسعير)[^\n]*\n(.*?)(?=^#|\Z)", spec, re.I | re.M | re.S)
    lines = [ln.strip() for ln in (m.group(2) if m else "").splitlines() if ln.strip()]
    return lines[:6]


def handle_output(run: Run, key: str, file: str, raw: str, index: int) -> str:
    """Apply the rules to one finished task and save it. Returns the text shown on the dashboard."""
    name = f"{index:02d}_{key}_{file}"
    if key == "karim":
        return save_site(run, key, file, raw, name)
    if key == "omar":
        price = price_section(raw)
        ans = run.ask("omar", "اقتراحي للسعر:\n" + ("\n".join(price) or "(مفيش سعر في المواصفات)") + "\nموافق عليه؟",
                      ["موافق", "سعر تاني (اكتبه)"])
        if ans["text"] or ans["choice"] != "موافق":
            raw += f"\n\n## The owner's decision on the price\n{ans['text'] or 'Not approved yet.'}\n"
    if key == "hassan":
        return make_video(run, raw, name)
    if key == "adam":
        raw, n = rules.remove_phone_numbers(raw)
        if n:
            run.log("adam", f"RULE: removed {n} phone number(s)/WhatsApp link(s), replaced with the website.")
    if key == "ziad":
        return save_leads(run, raw, name)
    run.write(name, raw)
    return raw


def make_video(run: Run, raw: str, name: str) -> str:
    """Hassan's scenes become an MP4 in output/videos/."""
    data = rules.extract_json(raw)
    if not isinstance(data, dict):
        run.update("hassan", "السيناريو اللي كتبته مش مظبوط، محتاج أكتبه تاني")
        run.write(name.replace(".json", "_invalid.txt"), raw)
        return "The video scenes were not valid JSON."
    spec = video.clean_spec(data, video.built_sites())
    run.write(name, json.dumps(spec, ensure_ascii=False, indent=1))
    out = OUTPUT_DIR / "videos" / f"{run.dir.name[:17]}_{rules.slug(spec['title'])[:30]}.mp4"
    run.update("hassan", f"بصوّر الفيديو دلوقتي ({len(spec['scenes'])} مشاهد)…")
    try:
        video.render(spec, out)
    except Exception as e:
        run.log("hassan", f"Video failed: {e}")
        run.update("hassan", f"مقدرتش أطلّع الفيديو: {e}")
        return f"Video failed: {e}"
    run.status["video"] = str(out.relative_to(OUTPUT_DIR))
    run.add_file(out)
    run.update("hassan", "الفيديو جاهز ✓ شوفه وقولي رأيك 👍/👎 عشان أتعلم ذوقك")
    return json.dumps(spec, ensure_ascii=False, indent=1)


def save_leads(run: Run, raw: str, name: str) -> str:
    data = rules.extract_json(raw)
    leads_info = run.status["leads"]
    if not isinstance(data, dict):
        # Without the structure we cannot check every name against contacted.json, so nothing is kept.
        run.log("ziad", "ERROR: answer was not valid JSON, so messages could not be checked and were dropped.")
        leads_info["error"] = "Ziad's answer was not in the expected format. Run Ziad again."
        run.save()
        return leads_info["error"]
    contacted = rules.load_contacted()
    allowed = {rules.normalize_name(n) for n in run.status["names"]}
    leads = []
    for lead in data.get("leads") or []:
        biz = str(lead.get("business", "")).strip()
        if not biz:
            continue
        if rules.is_contacted(biz, contacted):
            leads_info["skipped_contacted"].append(biz)
            run.log("ziad", f"RULE: dropped message to already-contacted '{biz}'.")
            continue
        if allowed and rules.normalize_name(biz) not in allowed:
            run.log("ziad", f"Dropped '{biz}': not in the owner's list.")
            continue
        msg, _ = rules.remove_phone_numbers(str(lead.get("message", "")))
        leads.append({"business": biz, "message": msg})
    leads_info["leads"] = leads
    leads_info["targets"] = [t for t in (data.get("targets") or []) if isinstance(t, dict)]
    md = ["# Lead list\n"]
    for t in leads_info["targets"]:
        md.append(f"## {t.get('kind', '')}\n{t.get('why', '')}\n\nTemplate:\n\n{t.get('template', '')}\n")
    if leads:
        md.append("# Personal messages\n")
        md += [f"## {l['business']}\n{l['message']}\n" for l in leads]
    if leads_info["skipped_contacted"]:
        md.append("# ⚠️ Already contacted (no message drafted, ask before contacting again)\n")
        md += [f"- {b}" for b in dict.fromkeys(leads_info["skipped_contacted"])]
    text = "\n".join(md)
    run.write(name, text)
    if leads or leads_info["targets"]:
        ans = run.ask("ziad", f"كتبت {len(leads)} رسايل و{len(leads_info['targets'])} قوالب، شوفهم في Work. أعتمدهم؟",
                      ["اعتمدهم", "ارفضهم"])
        leads_info["approved"] = ans["choice"] == "اعتمدهم"
        leads_info["note"] = ans["text"]
        if not leads_info["approved"]:
            leads_info["leads"], leads_info["targets"] = [], []
        run.save()
    return text


def handoff(run: Run, key: str, file: str, text: str, nxt: str | None):
    """What a teammate says when passing the work on (and when something needs fixing)."""
    if key == "mostafa":
        n = sum(1 for line in text.splitlines() if line.strip()[:3].rstrip(".)").isdigit())
        ok = "NEEDS FIX" not in text.upper()
        run.say("mostafa", "karim", "راجعت كل حاجة، تمام كده 👌" if ok else f"لقيت {n or 'شوية'} حاجات محتاجة تتصلح، بعتهالك بالتفصيل")
        return
    if key == "ziad" and (run.status.get("leads") or {}).get("skipped_contacted"):
        n = len(set(run.status["leads"]["skipped_contacted"]))
        run.say("ziad", "layla", f"فيه {n} أماكن اتكلمنا معاهم قبل كده، مكتبتلهمش حاجة. تحبي نكلمهم تاني؟")
    if key == "karim":
        if "draft" in file:
            run.say("karim", "mostafa", "الموقع جاهز، راجعه يا مصطفى")
        elif run.status["agents"]["mostafa"]["status"] != "idle":
            run.say("karim", "mostafa", "صلحت كل ملاحظاتك ✓")
        return
    lines = {"omar": "المواصفات والسعر جاهزين، اتفضل اكتب النصوص", "youssef": "النصوص جاهزة عربي وإنجليزي، اتفضل يا كريم"}
    if key in lines and nxt and nxt != key:
        run.say(key, nxt, lines[key])


# ---------------------------------------------------------------- the job
WHAT = {"spec": "مواصفات المشروع والسعر", "content": "نصوص الموقع عربي وإنجليزي", "website_draft": "أول نسخة من الموقع",
        "website": "النسخة النهائية من الموقع", "review": "مراجعة شغل كريم", "leads": "قايمة الأماكن ورسايل التواصل",
        "social": "أفكار وسكريبتات الفيديو", "video": "الفيديو"}


def _kickoff(run: Run, steps: list[tuple[Task, str, str]], first_index: int):
    """Run tasks in order; statuses and files update as each one finishes."""
    keys_in_order = [k for _, k, _ in steps]
    base = len(run.status["tasks"])

    for n, (task, key, file) in enumerate(steps):
        run.status["tasks"].append({"title": f"{TEAM[key]['name']}: {file}", "agent": key, "file": file, "done": False})

        def done(output, n=n, key=key, file=file):
            text = handle_output(run, key, file, output.raw, first_index + n)
            run.status["tasks"][base + n]["done"] = True
            run.log(key, f"Finished: {file}")
            later = keys_in_order[n + 1:]
            handoff(run, key, file, text, later[0] if later else None)
            run.set_agent(key, "waiting" if key in later else "done", text)
            if key == "omar":
                output.raw = text  # the price decision reaches the next teammates
            if later:
                run.current = later[0]
                run.set_agent(later[0], "working")
                run.log(later[0], "Started")
                run.update(later[0], "بشتغل دلوقتي على " + WHAT.get(steps[n + 1][2].split(".")[0], steps[n + 1][2]))

        task.callback = done
    for k in dict.fromkeys(keys_in_order):
        run.set_agent(k, "waiting")
    run.current = keys_in_order[0]
    run.set_agent(run.current, "working")
    run.log(run.current, "Started")
    run.update(run.current, "بشتغل دلوقتي على " + WHAT.get(steps[0][2].split(".")[0], steps[0][2]))

    def step(s):
        text = getattr(s, "thought", "") or getattr(s, "text", "") or getattr(s, "output", "") or str(s)
        run.log(run.current, "step: " + " ".join(str(text).split())[:300])

    run.steps = steps
    agents = list({id(t.agent): t.agent for t, _, _ in steps}.values())
    Crew(agents=agents, tasks=[t for t, _, _ in steps], process=Process.sequential,
         step_callback=step, max_rpm=MAX_RPM, verbose=False).kickoff()


def _task_row(run: Run, key: str, title: str) -> dict:
    row = {"title": f"{TEAM[key]['name']}: {title}", "agent": key, "file": "", "done": False}
    run.status["tasks"].append(row)
    run.current = key
    run.set_agent(key, "working")
    return row


def test_site(run: Run, agents: dict, keys: list[str]):
    """Tarek opens the site like a visitor; if it isn't client-ready, Karim fixes what he saw and Tarek tests again."""
    brief = f"{run.status['goal']} {run.status['client']}".strip()
    for rnd in range(1, TEST_ROUNDS + 1):
        row = _task_row(run, "tarek", f"test round {rnd}")
        run.say("tarek", "karim", "بفتح الموقع على الكمبيوتر والموبايل وبجربه زي الزبون…")
        try:
            shots = tester.shoot(run.site_dir, run.dir / "shots", f"r{rnd}")
            for s in shots:
                run.add_file(s)
            result = tester.judge(shots, brief, tester.TEMPLATE_NOTES.get(run.kind, "") + "\n" + knowledge.taste("site", 1500)
                                  + knowledge.skills("tarek"))
        except Exception as e:  # no Chrome / no Gemini key / busy: say so instead of pretending it was tested
            run.log("tarek", f"Couldn't test: {e}")
            run.say("tarek", "layla", f"مقدرتش أجرب الموقع: {e}")
            row["done"] = True
            run.set_agent("tarek", "error", f"Couldn't test: {e}")
            return
        result["round"] = rnd
        run.status["test"] = result
        rep = tester.report(result)
        run.write(f"{len(run.status['tasks']):02d}_tarek_test_r{rnd}.md", rep)
        row["done"] = True
        top = (result.get("problems") or [{}])[0]
        if result["verdict"] == "PASS":
            run.say("tarek", "layla", f"جربته على الكمبيوتر والموبايل: {result['score']:g}/10، جاهز للعميل ✓")
            run.set_agent("tarek", "done", rep)
            return
        last = rnd == TEST_ROUNDS or "karim" not in keys
        run.say("tarek", "karim", f"{result['score']:g}/10 لسه مش جاهز. أهم حاجة: {top.get('problem', '')} → {top.get('fix', '')}"
                + (" (وقفت هنا، محتاج قرارك)" if last else ""))
        run.set_agent("tarek", "done" if last else "waiting", rep)
        if last:
            return
        prow = _task_row(run, "karim", f"fix Tarek's notes (round {rnd})")
        ext = ".json" if run.kind in templates.FOLDER else ".html"
        fix = Task(
            description=f"Tarek tested the website in a real browser and found these problems:\n{rep}\n\n"
                        + "".join(f"The owner also said (follow it): {m}\n" for m in run.inbox) +
                        f"This is the current site content:\n{run.site_text}\n\n{karim_brief(run.kind)}\n\n"
                        "Fix every problem Tarek listed and return the whole corrected "
                        + ("JSON object only." if ext == ".json" else "HTML document only."),
            expected_output="The corrected site.", agent=agents["karim"], context=[])
        Crew(agents=[agents["karim"]], tasks=[fix], max_rpm=MAX_RPM, verbose=False).kickoff()
        out = save_site(run, "karim", "website" + ext, fix.output.raw, f"{len(run.status['tasks']):02d}_karim_polish_r{rnd}{ext}")
        prow["done"] = True
        run.set_agent("karim", "done", out)
        run.say("karim", "tarek", "صلحت اللي قلت عليه، جرب تاني يا طارق")


def _revise(run: Run, agents: dict, base: dict):
    """The owner's correction to the last site: Karim applies it, Tarek tests again."""
    site = OUTPUT_DIR / base["site"]
    run.site_dir = site.parent
    data_js = run.site_dir / "data.js"
    if data_js.is_file():
        run.kind, js = "cafe", data_js.read_text(encoding="utf-8")
        run.site_text = js[js.index("{"):js.rindex("}") + 1]
    else:
        run.kind, run.site_text = templates.pick(base["goal"]), site.read_text(encoding="utf-8")
    note = run.status["goal"].split("CORRECTION FROM THE OWNER:", 1)[-1].strip()
    run.say("you", "karim", note)
    row = _task_row(run, "karim", "apply your correction")
    run.update("karim", "تمام، بعدّل دلوقتي")
    ext = ".json" if run.kind in templates.FOLDER else ".html"
    fix = Task(description=f"The owner wants this change to the website:\n\"\"\"{note}\"\"\"\n\nCurrent site content:\n{run.site_text}\n\n"
                           f"{karim_brief(run.kind)}\n\nApply exactly the owner's change, keep everything else, and return the "
                           + ("whole JSON object only." if ext == ".json" else "whole HTML document only."),
               expected_output="The corrected site.", agent=agents["karim"], context=[])
    Crew(agents=[agents["karim"]], tasks=[fix], max_rpm=MAX_RPM, verbose=False).kickoff()
    out = save_site(run, "karim", "website" + ext, fix.output.raw, f"01_karim_revision{ext}")
    row["done"] = True
    run.set_agent("karim", "done", out)
    run.say("karim", "tarek", "عدلت اللي المدير طلبه، جربه يا طارق")
    test_site(run, agents, ["karim", "tarek"])
    run.status["state"] = "done"
    run.log("system", "Revision finished")


def _job(run: Run, mode: str, keys: list[str], base: dict | None = None):
    try:
        if mode == "ops":  # a laptop/GitHub action from the chat: no AI needed, the owner approves each step
            ops.handle(run, run.status["goal"])
            run.status["state"] = "done"
            return
        if mode == "advice":  # the owner asked a question: Layla answers from the playbook, about anything
            run.set_agent("layla", "working")
            ans = advise(run.status["goal"])
            run.say("layla", "you", ans, full=True)
            run.set_agent("layla", "done", ans)
            run.status["state"] = "done"
            return
        config.on_switch = lambda msg: run.log("system", msg)
        goal, client, names = run.status["goal"], run.status["client"], run.status["names"]
        agents = {k: make_agent(k, get_llm(JOB.get(k, "write"))) for k in ["layla", *ORDER]}
        if mode == "whole":
            run.log("layla", f"Planning with {run.status['llm']}")
            run.set_agent("layla", "working")
            t = plan_task(goal, agents["layla"])
            Crew(agents=[agents["layla"]], tasks=[t], verbose=False).kickoff()
            plan = parse_plan(t.output.raw, goal)
            keys = plan["agents"]
            client = client or plan["client_name"]
            names = names or plan["business_names"]
            run.status.update(client=client, names=names, plan=plan)
            run.write("00_layla_plan.json", json.dumps(plan, ensure_ascii=False, indent=2))
            team = "، ".join(TEAM[k]["name"] for k in keys)
            run.log("layla", f"Team: {team}. {plan['reason']}")
            run.say("layla", keys[0], f"يلا يا جماعة: {team}. ابدأ انت يا {TEAM[keys[0]]['name']}")
            run.set_agent("layla", "waiting", f"Team: {team}\n\n{plan['reason']}")
        if mode == "revise":
            return _revise(run, agents, base)
        crew_keys = [k for k in keys if k != "tarek"]  # Tarek works after the site exists, outside the crew
        steps = build_tasks(crew_keys, goal, client, names, agents, run) if crew_keys else []
        if steps:
            _kickoff(run, steps, first_index=1)
        if "tarek" in keys:
            if run.site_text:
                test_site(run, agents, keys)
            else:
                run.say("tarek", "layla", "مفيش موقع أجربه في الرن ده")
                run.set_agent("tarek", "done", "No website to test in this run.")
        if mode == "whole":
            outputs = "\n\n".join(f"--- {TEAM[k]['name']} ({f}) ---\n{(t.output.raw or '')[:3000]}"
                                  for t, k, f in steps)
            test = run.status.get("test")
            if test:
                outputs += f"\n\n--- Tarek (browser test) ---\n{tester.report(test)}"
            summary = Task(
                description=f"The owner asked:\n\"\"\"{run.status['goal']}\"\"\"\n\nYour team's work "
                            f"(long outputs are cut):\n{outputs}\n\nFiles saved: {', '.join(run.status['files'][:40])}\n\n"
                            "Write the final summary for the owner in Egyptian Arabic, at most 6 short bullet lines: "
                            "what was done and by whom, the main file or link, anything that needs his decision "
                            "(e.g. price, already-contacted businesses), and the one next step. No filler.",
                expected_output="At most 6 short Markdown bullets.", agent=agents["layla"], context=[])
            run.set_agent("layla", "working")
            run.current = "layla"
            run.status["tasks"].append({"title": "Layla: final summary", "agent": "layla", "file": "summary.md", "done": False})
            Crew(agents=[agents["layla"]], tasks=[summary], verbose=False).kickoff()
            run.write("99_layla_summary.md", summary.output.raw)
            run.status["tasks"][-1]["done"] = True
            run.set_agent("layla", "done", summary.output.raw)
        run.status["state"] = "done"
        run.log("system", "Run finished")
    except Exception as e:  # shown on the dashboard instead of dying silently in the thread
        run.status["state"] = "error"
        run.status["error"] = f"{type(e).__name__}: {e}"
        if run.current in run.status["agents"]:
            run.status["agents"][run.current]["status"] = "error"
        run.log("system", "ERROR " + traceback.format_exc())
    finally:
        run.status["finished"] = datetime.now().isoformat(timespec="seconds")
        run.save()


def start(goal: str, mode: str, keys: list[str] | None = None, client: str = "", names: list[str] | None = None,
          base: dict | None = None) -> str:
    """Start a run in the background. mode: 'whole' (Layla picks the team) or 'focused' (you pick). Returns run id."""
    goal = goal.strip()
    if not goal:
        raise ValueError("Write a task first.")
    keys = [k for k in ORDER if k in (keys or [])]
    if mode == "focused" and not keys:
        raise ValueError("Pick at least one team member.")
    with _lock:
        if _active["thread"] and _active["thread"].is_alive():
            raise RuntimeError("A run is already in progress. Wait for it to finish.")
        run = Run(goal, mode, client.strip(), [n.strip() for n in (names or []) if n.strip()])
        run.log("system", f"Mode: {mode}. LLM: {run.status['llm']}. Goal: {goal}")
        th = threading.Thread(target=_job, args=(run, mode, keys, base), daemon=True)
        _active["thread"], _active["run"] = th, run
        th.start()
    return run.status["id"]


def is_running() -> bool:
    return bool(_active["thread"] and _active["thread"].is_alive())


def load_status(run_id: str) -> dict | None:
    path = RUNS_DIR / run_id / "status.json"
    for _ in range(5):
        try:
            st = json.loads(path.read_text(encoding="utf-8"))
            live = active()
            if st.get("state") == "running" and not (live and live.status["id"] == run_id):
                st.update(state="stopped", error="Stopped: start.bat was closed while this run was working.", ask=None)
            return st
        except (FileNotFoundError, json.JSONDecodeError, PermissionError):
            time.sleep(0.05)
    return None


def list_runs() -> list[str]:
    if not RUNS_DIR.exists():
        return []
    return sorted((p.name for p in RUNS_DIR.iterdir() if (p / "status.json").exists()), reverse=True)


def active() -> Run | None:
    return _active["run"] if is_running() else None


def answer(run_id: str, qid: int, choice: str, text: str = ""):
    run = active()
    if not run or run.status["id"] != run_id:
        raise ValueError("That run isn't waiting for an answer anymore.")
    run.answer(int(qid), str(choice), str(text))


def is_question(text: str) -> bool:
    """A question or a 'what if' for Layla, as opposed to a change to the last website."""
    t = text.strip()
    return t.endswith(("?", "؟")) or bool(re.match(
        r"(إزاي|ازاي|ليه|إيه|ايه|هل|أعمل إيه|اعمل ايه|لو (?!سمحت)|امتى|إمتى|فين|كام|ينفع|what|how|why|should|can|when)\b", t, re.I))


def advise(text: str) -> str:
    """Layla's short answer to the owner, from the playbook and his rules. About anything, not only websites."""
    q = Task(description=f"The owner (Asser) writes to you:\n\"\"\"{text}\"\"\"\n\nAnswer him in Egyptian Arabic, short "
                         "and practical: the answer first, then at most 5 numbered steps if steps help. Help with anything "
                         "(clients, prices, marketing, tech, business), not only websites. Use the playbook and his rules "
                         "below; if you don't know something, say so instead of guessing.\n\n"
                         f"PLAYBOOK:\n{knowledge.playbook()}\n\n{knowledge.taste()}",
             expected_output="A short answer in Egyptian Arabic.", agent=make_agent("layla", get_llm()), context=[])
    Crew(agents=[q.agent], tasks=[q], verbose=False).kickoff()
    return q.output.raw.strip()


EDIT = re.compile(r"عد[ّ]?ل|غي[ّ]?ر|صل[ّ]?ح|ضيف|زو[ّ]?د|شيل|امسح|خل[ّ]?ي|بد[ّ]?ل|كب[ّ]?ر|صغ[ّ]?ر|\b(change|fix|edit|add|remove|replace)\b", re.I)


def wants_new_site(text: str) -> bool:
    return wants_website(text) or bool(re.match(r"\s*(اعمل|اعملي|ابني|ابنيلي|صمم|صمملي)\s*(لي\s*)?(موقع|ويب|صفحة|سايت)", text))


def _answer_during_run(run: "Run", text: str):
    try:
        run.say("layla", "you", advise(text), full=True)
    except Exception as e:  # her answer failing must never touch the team's work
        run.log("system", f"Layla couldn't answer during the run: {e}")


def message(text: str) -> dict:
    """The owner writes in the chat. A laptop action → ops; a new site → a new job; a clear change ("عدل/غير/ضيف…")
    → the teammate he names (during a run) or Karim on the last site; anything else → Layla answers, and the work
    going on is never stopped or changed by it."""
    text = text.strip()
    if not text:
        raise ValueError("Write a message first.")
    run = active()
    if ops.intent(text):  # "اعمل ريبو …" / "شغّل git status" → done on the laptop after the owner approves
        if run:
            raise ValueError("فيه شغل شغال دلوقتي، ابعتها تاني لما يخلص.")
        return {"run": start(text, "ops", ["karim"])}
    if wants_new_site(text) and not EDIT.match(text.strip()):  # "اعمل موقع لمطعم" is a new job, not an edit of the last site
        if run:
            raise ValueError("فيه شغل شغال دلوقتي، ابعت طلب الموقع الجديد لما يخلص.")
        return {"run": start(text, "whole")}
    if is_question(text) or not EDIT.search(text):  # a question or a chat: Layla answers, the work keeps going
        if not run:
            return {"run": start(text, "advice", ["layla"])}
        run.say("you", "layla", text)
        threading.Thread(target=_answer_during_run, args=(run, text), daemon=True).start()
        return {"run": run.status["id"], "to": "layla"}
    if run:
        target = next((k for k, a in TEAM.items() if a["name"].lower() in text.lower() or a.get("ar", "~") in text), run.current)
        run.say("you", target, text)
        run.inbox.append(text)
        todo = [t for t, k, _ in run.steps if t.output is None]
        mine = [t for t, k, _ in run.steps if k == target and t.output is None]
        for t in (mine or todo)[:1]:
            t.description += f"\n\nNEW INSTRUCTION FROM THE OWNER (follow it): {text}"
        return {"run": run.status["id"], "to": target}
    last = next((st for st in (load_status(r) for r in list_runs()) if st and st.get("site")), None)
    if not last:
        raise ValueError("No website to correct yet. Type a new goal at the top.")
    first = last["goal"].split("\n\nCORRECTION FROM THE OWNER:")[0]  # the original request, not every older correction
    goal = f"{first}\n\nCORRECTION FROM THE OWNER: {text}"
    return {"run": start(goal, "revise", ["karim", "tarek"], last.get("client", ""), [], base=last)}


def feedback(run_id: str, kind: str, vote: str, comment: str = "") -> dict:
    """👍/👎 on a run's website or video: saved to knowledge/, 👍 also keeps the work as an approved example."""
    st = load_status(run_id)
    if not st or kind not in ("site", "video") or vote not in ("up", "down"):
        raise ValueError("Unknown run, kind or vote.")
    files = []
    if kind == "site" and st.get("site"):
        site = OUTPUT_DIR / st["site"]
        files = [site.parent / "data.js" if (site.parent / "data.js").is_file() else site]
        shots = sorted((RUNS_DIR / run_id / "shots").glob("*_desktop_1.png")) if (RUNS_DIR / run_id / "shots").exists() else []
        files += shots[-1:]
    elif kind == "video" and st.get("video"):
        files = [OUTPUT_DIR / st["video"], *sorted((RUNS_DIR / run_id).glob("*_hassan_video.json"))]
    else:
        raise ValueError("This run has no " + kind + ".")
    knowledge.add_feedback(kind, vote, comment, st.get("client") or st["goal"][:40], files)
    fb = {**st.get("feedback", {}), kind: {"vote": vote, "comment": comment.strip()}}
    run = _active["run"]
    if run and run.status["id"] == run_id:
        run.status["feedback"] = fb
        run.save()
    else:
        st["feedback"] = fb
        (RUNS_DIR / run_id / "status.json").write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    return fb


def publish(run_id: str, name: str) -> str:
    """The owner pressed Publish and confirmed: put the run's website on GitHub Pages. Returns the live URL."""
    st = load_status(run_id)
    if not st or not st.get("site"):
        raise ValueError("This run has no website to publish.")
    site_dir = (OUTPUT_DIR / st["site"]).parent
    blockers = [p for p in security.scan_site(site_dir) if p.startswith("HIGH")]
    if blockers:
        raise ValueError("Not published: " + "; ".join(blockers))
    try:
        url = publisher.to_github(site_dir, name)
    except (OSError, subprocess.SubprocessError) as e:  # no internet, git missing or too slow
        raise RuntimeError(f"Publishing failed: {e}") from e
    run = _active["run"]
    if run and run.status["id"] == run_id:
        run.status["published"] = url
        run.log("layla", f"Published on GitHub Pages: {url} (live in about a minute).")
        run.save()
    else:
        st["published"] = url
        (RUNS_DIR / run_id / "status.json").write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    return url
