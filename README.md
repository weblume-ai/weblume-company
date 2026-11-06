# Weblume AI Company

A team of 7 AI employees for **Weblume** ("Websites that make an impact"), built with Python + CrewAI, with a
local dashboard in Weblume colors: a live 3D office where you watch the team work.

| Agent | Job | Saves |
|---|---|---|
| 👩‍💼 Layla, CEO | Picks the team (whole-company mode) and writes the final summary | `00_layla_plan.json`, `99_layla_summary.md` |
| 🧭 Omar, Client Analyst | Brief → spec: pages, sections, features, style, price range | `spec.md` |
| ✍️ Nour, Copywriter | Website copy in Egyptian Arabic + English | `content.md` |
| 💻 Karim, Front-end | One-file animated website, edited from a ready Weblume template | `website.html` + `output/<client>/index.html` |
| 🔍 Hana, Reviewer | Bugs, mobile layout, spelling, SEO; sends fixes back to Karim | `review.md` |
| 🎯 Ziad, Lead Finder | Target businesses + personal outreach messages | `leads.md` |
| 📱 Sara, Social Media | TikTok/Instagram ideas, scripts, captions | `social.md` |

## Rules the code enforces (not just "asks" the AI)
- **Ziad never messages a business twice.** Every name you give him is checked against `contacted.json`
  *before* he writes anything (spelling, capitals, accents and Arabic tashkeel are ignored). Already-contacted
  ones are flagged on the dashboard, not drafted. After you really send a message, click **✔ Mark as
  contacted** on the dashboard (or add a name on the Home tab) so it's remembered. If you give no names, he
  writes templates with `[اسم المكان]`, never fake businesses.
- **Sara never shows a phone number.** Any phone number or WhatsApp link in her output is replaced with the
  Weblume website, and the log says so.

## Modes
- **Whole company**: you write the goal, Layla decides who is needed, they work in order, Layla summarizes.
- **Focused team**: you pick the people (e.g. only Karim + Hana).

Work order is always Omar → Nour → Karim → Hana → Karim (fixes) → Ziad → Sara.

## Folder structure
```
weblume-company/
├── server.py              Dashboard server (built-in Python, no extra packages)
├── index.html             The dashboard page: 3D office + Home / Work / Progress / Team tabs
├── start.bat              Double-click to open the dashboard
├── requirements.txt
├── .env.example           Copy to .env (your settings and keys)
├── contacted.json         Businesses already contacted (Ziad never drafts for these)
├── weblume/
│   ├── config.py          Reads .env, builds the AI model (Gemini / Groq / Ollama)
│   ├── team.py            The 7 agents: name, role, goal, backstory
│   ├── company.py         Plans the work, runs the agents, saves files, live status, log
│   ├── rules.py           contacted.json + phone-number rules, cleaning AI answers
│   └── templates/         Karim's starting points (see below)
│       ├── cafe.html      Cafés, restaurants, bakeries: menu tabs, WhatsApp order buttons
│       ├── clinic.html    Clinics and services: booking form that sends to WhatsApp, steps, FAQ
│       ├── shop.html      Stores and brands: product filters, cart that sends the order on WhatsApp
│       ├── motion.css/js  The animation kit, added to every site automatically
│       └── GUIDE.md       How Karim uses the kit (sent to him with the template)
├── tests/test_rules.py    Checks for the rules
└── output/
    ├── <client-name>/index.html          Final website
    └── runs/<date_time_task>/            Every run: numbered files + run.log + status.json
```

## Install on Windows (step by step, once)

1. **Install Python 3.12** from https://www.python.org/downloads/windows/ (CrewAI needs 3.10 to 3.13).
   In the installer, **tick "Add python.exe to PATH"**, then click Install Now.
   - If typing `python` later opens the Microsoft Store: Settings → Apps → Advanced app settings →
     App execution aliases → turn off the two "python" entries.
2. **Open a terminal in this folder**: open the `weblume-company` folder in File Explorer, click the address
   bar, type `powershell`, press Enter.
3. **Create the environment and install** (takes a few minutes):
   ```
   python -m venv .venv
   .venv\Scripts\python -m pip install -r requirements.txt
   ```
4. **Add your settings**:
   ```
   copy .env.example .env
   notepad .env
   ```
   Paste your free Gemini key after `GEMINI_API_KEY=` (get it at https://aistudio.google.com/apikey), save.
5. **Run**: double-click `start.bat` (or `.venv\Scripts\python server.py`).
   The dashboard opens at http://127.0.0.1:8501. Keep the black window open while you use it.

Check the rules any time: `.venv\Scripts\python tests\test_rules.py`

## Website templates and animations
Karim never starts from a blank page. The code picks the template that fits the request (café, clinic or
shop; café if unsure), and Karim edits it: the client's content, brand colors, WhatsApp number, sections.
The animation kit is added by the code after he finishes, so the animations can't be broken or lost:
page loader, scroll progress bar, reveal on scroll, headings rising word by word, endless marquee strip,
3D tilt cards, magnetic buttons, light sweep, counters, parallax, floating badges, cursor glow, mobile
menu, Arabic/English switch, WhatsApp buttons. It respects "reduce motion" and needs no library.
To add a template: put `name.html` in `weblume/templates/` with the two `<!--WEBLUME:...-->` markers and
add its keywords to `KINDS` in `weblume/templates/__init__.py`.

## The dashboard
Two ways to open it, both need `start.bat` running on your laptop (that's where the team works):
- **On the laptop**: http://127.0.0.1:8501 (start.bat opens it).
- **Online link**: https://weblume-ai.github.io/weblume-company/ connects to start.bat on the same
  computer. Chrome asks once about *local network access*: choose **Allow**. Without start.bat the
  page shows "Not connected". The server accepts only this link and 127.0.0.1, no other site.

- **Top bar**: Whole company / Focused team (pick people), the goal box, **Start goal**, a Live light, and
  **Hide 3D** for slow devices.
- **3D office**: one room per person, plus a lounge. Free people walk around; working people sit at their
  desk and their screen glows red; waiting people stand by their desk with a red mark; ✓ means done.
  Drag to turn the view, scroll to zoom, click a name to follow that person.
- **Home**: model in use, current run with % done, client name, business names for Ziad, past runs,
  contacted list. **Work**: each person's output, Ziad's leads (Copy / Mark as contacted), files to open or
  download. **Progress**: task checklist and the log. **Team**: the 7 people and their status.
- The 3D office loads three.js from the internet; offline (Ollama), the panel still works without it.

## Switching the AI (edit `.env`, then restart start.bat)
- **Gemini (default, free)**: `LLM_PROVIDER=gemini` + `GEMINI_API_KEY`.
- **Groq (free, very fast)**: `LLM_PROVIDER=groq` + `GROQ_API_KEY` from https://console.groq.com/keys.
  Its free limits are small for long websites; use it for Ziad/Sara, Gemini for websites.
- **Ollama (your laptop, offline, free)**: `LLM_PROVIDER=ollama`. Install Ollama from https://ollama.com, then:
  ```
  ollama pull qwen2.5:7b
  ```
  Keep it 7B–8B on the RTX 4060 8 GB (`qwen2.5:7b`, `llama3.1:8b`, or your own `weblume` model via
  `LLM_MODEL=weblume`). Give Ollama more memory for long prompts: Windows search → "environment variables" →
  New user variable `OLLAMA_CONTEXT_LENGTH` = `16384`, then restart Ollama. Small local models write weaker
  websites and sometimes break the JSON Layla/Ziad must return; the app then falls back safely (Layla) or
  tells you to run again (Ziad).

## Troubleshooting
| Problem | Fix |
|---|---|
| `GEMINI_API_KEY is empty` | Put the key in `.env` (not `.env.example`) and restart |
| `429` / rate limit | Free tier limit. Wait a minute, or lower `MAX_REQUESTS_PER_MINUTE` in `.env` |
| `start.bat` says run setup first | Do steps 1–3 above |
| Ollama: connection refused | Open the Ollama app (it must be running) |
| Website file looks cut off | Use Gemini for websites; small local models stop early |

Not included: sending messages (you send them yourself), real Google Maps search (paste the names you find).
