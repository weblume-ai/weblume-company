"""Runs the company: plans the work, runs the agents in order, saves every output and a live status file."""
import json
import os
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

from crewai import Crew, Process, Task

from . import config, rules, templates
from .config import CURRENCY, MAX_RPM, OUTPUT_DIR, PROVIDER, RUNS_DIR, WEBSITE, get_llm, model_name
from .team import ORDER, TEAM, make_agent

_lock = threading.Lock()
_active: dict = {"thread": None}


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
            "tasks": [], "files": [], "leads": None,
        }
        self.current = "layla"
        self.save()

    def save(self):
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

    def set_agent(self, key: str, status: str, output: str | None = None):
        self.status["agents"][key]["status"] = status
        if output is not None:
            self.status["agents"][key]["output"] = output
        self.save()

    def write(self, name: str, text: str, copy_to: Path | None = None) -> Path:
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        self.status["files"].append(str(path.relative_to(OUTPUT_DIR)))
        if copy_to:
            copy_to.parent.mkdir(parents=True, exist_ok=True)
            copy_to.write_text(text, encoding="utf-8")
            self.status["files"].append(str(copy_to.relative_to(OUTPUT_DIR)))
        self.save()
        return path


# ---------------------------------------------------------------- planning
PLAN_HINT = {
    "omar": "client brief -> project spec and price",
    "nour": "website copy in Egyptian Arabic + English",
    "karim": "builds the website (HTML file)",
    "hana": "reviews code and copy, sends fixes to Karim",
    "ziad": "lead finding and outreach messages",
    "sara": "TikTok / Instagram ideas, scripts, captions",
}


def plan_task(goal: str, agent) -> Task:
    team = "\n".join(f"- {k}: {TEAM[k]['name']} ({v})" for k, v in PLAN_HINT.items())
    return Task(
        description=(
            f"The owner of Weblume asked:\n\"\"\"{goal}\"\"\"\n\n"
            f"Your team:\n{team}\n\n"
            "Decide who is needed. A new website normally needs omar, nour, karim and hana. "
            "Pick only who the request really needs.\n"
            "Also pull out the client/business name if the request is about one client's website, and any "
            "real business names the owner listed for outreach.\n"
            "Answer with JSON only, no other text, exactly in this shape:\n"
            '{"agents": [<the keys you chose>], "client_name": "", "business_names": [], "reason": "one sentence"}'
        ),
        expected_output="A JSON object with agents, client_name, business_names and reason.",
        agent=agent,
    )


WEBSITE_TEAM = ["omar", "nour", "karim", "hana"]


def wants_website(goal: str) -> bool:
    g = goal.lower()
    return any(w in g for w in ["build a site", "website", "landing page", "اعمل موقع", "موقع ل", "صفحة هبوط"])


def keyword_plan(goal: str) -> list[str]:
    """Fallback when Layla's answer is not valid JSON."""
    g = goal.lower()
    picks = []
    if any(w in g for w in ["lead", "outreach", "عملاء", "رسايل", "رسائل", "تواصل مع"]):
        picks.append("ziad")
    if any(w in g for w in ["tiktok", "instagram", "reel", "تيك", "انستا", "فيديو", "caption", "كابشن"]):
        picks.append("sara")
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
def build_tasks(keys: list[str], goal: str, client: str, names: list[str], agents: dict, run: Run) -> list[tuple]:
    """Tasks for the chosen agents, always in company order. Each entry: (Task, agent key, output file)."""
    t: dict[str, Task] = {}
    steps: list[tuple[Task, str, str]] = []
    site_path = OUTPUT_DIR / rules.slug(client or goal[:30]) / "index.html"

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
            "gallery, Arabic/English switch), Style direction (mood, colors, fonts, photos to use), "
            f"Suggested price range in {CURRENCY} (basic and with extras, with a one-line reason), "
            "Questions to ask the client. Do not invent facts about the client; mark unknowns as TODO.",
            "A Markdown project spec with all the headings above.", [])
    if "nour" in keys:
        add("copy", "nour", "content.md",
            f"Request:\n\"\"\"{goal}\"\"\"\n\nWrite the website copy for every page and section in the spec "
            "(or in the request if there is no spec). For each section give: Arabic (Egyptian dialect) and "
            "English. Include page titles, meta descriptions (under 155 characters), headlines, short body text "
            "and button labels. No fake reviews, numbers or awards.",
            "Markdown copy, section by section, Arabic then English.", [t.get("spec")])
    if "karim" in keys:
        kind = templates.pick(f"{goal} {client}")
        run.log("karim", f"Template: {kind}")
        add("build", "karim", "website_draft.html" if "hana" in keys else "website.html",
            f"Request:\n\"\"\"{goal}\"\"\"\n\nBuild the website by EDITING the ready Weblume template below. "
            "Fill it with the real content from the spec and copy you were given (Arabic in the markup, English "
            "in data-en), set the client's brand colors in the :root variables, keep the sections the client "
            "needs, remove the rest, add sections the spec asks for using the same classes, and put the client's "
            "WhatsApp number in <body data-wa>. Keep it one file, mobile-first, with <title>, meta description "
            "and Open Graph filled in.\n"
            "NEVER invent reviews, testimonials, ratings, years, customer counts or awards: use only what the "
            "request or spec gives; otherwise delete that counter, badge or section. NEVER use stock photo links "
            "(Unsplash, Pexels…): keep the .ph placeholders unless the request gives real image URLs.\n\n"
            f"HOW THE ANIMATIONS WORK (follow this exactly):\n{templates.guide()}\n\n"
            f"THE TEMPLATE ({kind}):\n{templates.load(kind)}\n\n"
            "Output ONLY the full edited HTML document from <!DOCTYPE html> to </html>, nothing before or after.",
            "One complete HTML document based on the template.", [t.get("spec"), t.get("copy")])
    if "hana" in keys:
        add("review", "hana", "review.md",
            f"Request:\n\"\"\"{goal}\"\"\"\n\nReview the work you were given. Check: bugs in HTML/CSS/JS, layout "
            "on a 375px phone (overflow, tiny tap targets, text too small), RTL issues, spelling in Arabic and "
            "English, SEO basics (title, meta description, one h1, alt text, Open Graph), and that the copy "
            "matches the spec. If the site is built on a Weblume template, the animations come from the motion kit "
            "injected at the <!--WEBLUME:...--> markers: do not ask to remove the markers or to add an animation "
            "library; do check the kit's classes are used as documented. "
            "List every problem as: where -> what is wrong -> exact fix. End with a verdict "
            "line: READY or NEEDS FIXES.",
            "A Markdown review: a numbered list of problems with exact fixes, then the verdict.",
            [t.get("build"), t.get("copy"), t.get("spec")])
    if "karim" in keys and "hana" in keys:
        add("fix", "karim", "website.html",
            "Hana reviewed your website. Apply every fix from her review to the website you built and return "
            "the whole corrected file. Keep the <!--WEBLUME:MOTION_CSS--> and <!--WEBLUME:MOTION_JS--> markers. "
            "Output ONLY the full HTML document from <!DOCTYPE html> to </html>.",
            "One complete, corrected HTML document.", [t["build"], t["review"]])
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
    if "sara" in keys:
        add("social", "sara", "social.md",
            f"Request:\n\"\"\"{goal}\"\"\"\n\nPlan TikTok / Instagram content for Weblume (black, red and white "
            "brand). For each video idea: title, hook (first 2 seconds), full short script with shots, on-screen "
            "text, caption in Egyptian Arabic, and hashtags. The call to action always sends people to the "
            f"Weblume website ({WEBSITE}). NEVER write a phone number or WhatsApp number anywhere.",
            "Markdown: numbered video ideas, each with hook, script, on-screen text, caption and hashtags.", [])
    run.site_path = site_path
    return steps


# ---------------------------------------------------------------- after each task
def handle_output(run: Run, key: str, file: str, raw: str, index: int) -> str:
    """Apply the rules to one finished task and save it. Returns the text shown on the dashboard."""
    name = f"{index:02d}_{key}_{file}"
    if file.endswith(".html"):
        html, stock = templates.strip_stock_photos(rules.extract_html(raw))
        html = templates.inject_motion(html)
        if stock:
            run.log(key, f"RULE: replaced {stock} stock photo(s) with placeholders for the client's real photos.")
        if file == "website.html":
            for claim in templates.claims_to_check(html):
                run.log(key, f"CHECK before sending: {claim}.")
        if "<html" not in html.lower():
            run.log(key, "WARNING: the answer does not look like a full HTML page; saved as is.")
        final = file == "website.html"
        run.write(name, html, copy_to=run.site_path if final else None)
        if final:
            run.log(key, f"Website saved to output/{run.site_path.relative_to(OUTPUT_DIR).as_posix()}")
        return html
    if key == "sara":
        raw, n = rules.remove_phone_numbers(raw)
        if n:
            run.log("sara", f"RULE: removed {n} phone number(s)/WhatsApp link(s), replaced with the website.")
    if key == "ziad":
        return save_leads(run, raw, name)
    run.write(name, raw)
    return raw


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
    return text


# ---------------------------------------------------------------- the job
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
            run.set_agent(key, "waiting" if key in later else "done", text)
            if later:
                run.current = later[0]
                run.set_agent(later[0], "working")
                run.log(later[0], "Started")

        task.callback = done
    for k in dict.fromkeys(keys_in_order):
        run.set_agent(k, "waiting")
    run.current = keys_in_order[0]
    run.set_agent(run.current, "working")
    run.log(run.current, "Started")

    def step(s):
        text = getattr(s, "thought", "") or getattr(s, "text", "") or getattr(s, "output", "") or str(s)
        run.log(run.current, "step: " + " ".join(str(text).split())[:300])

    agents = list({id(t.agent): t.agent for t, _, _ in steps}.values())
    Crew(agents=agents, tasks=[t for t, _, _ in steps], process=Process.sequential,
         step_callback=step, max_rpm=MAX_RPM, verbose=False).kickoff()


def _job(run: Run, mode: str, keys: list[str]):
    try:
        config.on_switch = lambda msg: run.log("system", msg)
        llm = get_llm()
        goal, client, names = run.status["goal"], run.status["client"], run.status["names"]
        agents = {k: make_agent(k, llm) for k in ["layla", *ORDER]}
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
            run.log("layla", f"Team: {', '.join(TEAM[k]['name'] for k in keys)}. {plan['reason']}")
            run.set_agent("layla", "waiting", f"Team: {', '.join(TEAM[k]['name'] for k in keys)}\n\n{plan['reason']}")
        steps = build_tasks(keys, goal, client, names, agents, run)
        _kickoff(run, steps, first_index=1)
        if mode == "whole":
            outputs = "\n\n".join(f"--- {TEAM[k]['name']} ({f}) ---\n{(t.output.raw or '')[:3000]}"
                                  for t, k, f in steps)
            summary = Task(
                description=f"The owner asked:\n\"\"\"{run.status['goal']}\"\"\"\n\nYour team's work "
                            f"(long outputs are cut):\n{outputs}\n\nFiles saved: {', '.join(run.status['files'])}\n\n"
                            "Write the final summary for the owner: what was done, by whom, the files, anything "
                            "that needs his decision (e.g. price, already-contacted businesses), next steps.",
                expected_output="A short Markdown summary.", agent=agents["layla"], context=[])
            run.set_agent("layla", "working")
            run.current = "layla"
            run.status["tasks"].append({"title": "Final summary", "agent": "layla", "file": "summary.md", "done": False})
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


def start(goal: str, mode: str, keys: list[str] | None = None, client: str = "", names: list[str] | None = None) -> str:
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
        th = threading.Thread(target=_job, args=(run, mode, keys), daemon=True)
        _active["thread"] = th
        th.start()
    return run.status["id"]


def is_running() -> bool:
    return bool(_active["thread"] and _active["thread"].is_alive())


def load_status(run_id: str) -> dict | None:
    path = RUNS_DIR / run_id / "status.json"
    for _ in range(5):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, PermissionError):
            time.sleep(0.05)
    return None


def list_runs() -> list[str]:
    if not RUNS_DIR.exists():
        return []
    return sorted((p.name for p in RUNS_DIR.iterdir() if (p / "status.json").exists()), reverse=True)
