# Weblume AI Company

A team of 9 AI employees for **Weblume** ("Websites that make an impact"), built with Python + CrewAI, with a
local dashboard in Weblume colors: a live 3D office where you watch the team work and talk to each other.

| Agent | Job | Saves |
|---|---|---|
| 👩‍💼 Layla, CEO | Picks the team (whole-company mode) and writes the final summary | `00_layla_plan.json`, `99_layla_summary.md` |
| 🧭 Omar, Client Analyst | Brief → spec: pages, sections, features, style, price range | `spec.md` |
| ✍️ Youssef, Copywriter | Website copy in Egyptian Arabic + English | `content.md` |
| 💻 Karim, Front-end | Makes Weblume's premium templates the client's own (the Loopie design for cafés) | `website.json` / `.html` + `output/<client>/` |
| 🔍 Mostafa, Reviewer | Checks Karim's code and content; sends fixes back to him | `review.md` |
| 🧪 Tarek, QA Tester | Opens the finished site in your real Chrome on desktop and phone, Gemini judges the screenshots out of 10; under 8, Karim fixes and Tarek tests again | `tarek_test_r1.md`, `shots/*.png` |
| 🎯 Ziad, Lead Finder | Target businesses + personal outreach messages | `leads.md` |
| 📱 Adam, Social Media | TikTok/Instagram ideas, scripts, captions | `social.md` |
| 🎬 Hassan, Video Producer | Turns Adam's script into a 9:16 MP4: animated Arabic text, Weblume branding, our sites scrolling in phone/laptop mockups | `output/videos/*.mp4` |

They talk to each other when they pass work on or find a problem ("لقيت 3 حاجات محتاجة تتصلح"): it shows as
a speech bubble in the 3D office (the speaker walks over) and in Progress → Team chat.

## Talk to them, and they ask you
- **Chat tab**: every teammate posts what they're doing now and what they finished, in Egyptian Arabic.
  Write to them anytime: name the person ("كريم غيّر اللون للأخضر") and it goes into their next task.
  With no run going, a message is a correction to the last website: Karim applies it and Tarek retests.
- **They stop and ask you** (buttons + an optional note), and wait for your answer:
  - Karim: which template to use (his suggestion first).
  - Omar: the project price he suggests (approve, or write your own).
  - Ziad: approve or reject the outreach messages before they count as final.
  Nothing is published or paid for, so there's no question for those yet.
- **Your taste**: under every website and video there's 👍 / 👎 + a comment. It's saved to
  `knowledge/feedback.md`; 👍 also keeps the work in `knowledge/examples/approved/`. Karim and Hassan read it
  before designing, and Mostafa and Tarek check new work against it. (These files stay on your laptop.)

## Rules the code enforces (not just "asks" the AI)
- **Ziad never messages a business twice.** Every name you give him is checked against `contacted.json`
  *before* he writes anything (spelling, capitals, accents and Arabic tashkeel are ignored). Already-contacted
  ones are flagged on the dashboard, not drafted. After you really send a message, click **✔ Mark as
  contacted** on the dashboard (or add a name on the Home tab) so it's remembered. If you give no names, he
  writes templates with `[اسم المكان]`, never fake businesses.
- **No phone numbers in content or videos.** Adam's text and every line of Hassan's videos are checked;
  a line with a number is replaced with "تواصل معانا من موقع Weblume", and every video ends on the website.
- **Adam never shows a phone number.** Any phone number or WhatsApp link in his output is replaced with the
  Weblume website, and the log says so.
- **No made-up prices or opening hours.** Prices and hours that aren't in your request are removed from the
  site (the page then hides them). Put the real menu prices and hours in the request.
- **No dead photos.** Photo links that don't load become labeled placeholders; image paths that don't exist
  are swapped for the template's photos. Reviews or ratings on a site are flagged "CHECK before sending".

## Modes
- **Whole company**: you write the goal, Layla decides who is needed, they work in order, Layla summarizes.
- **Focused team**: you pick the people (e.g. only Karim + Mostafa + Tarek).

Work order is always Omar → Youssef → Karim → Mostafa → Karim (fixes) → Tarek (test; Karim fixes, Tarek retests) → Ziad → Adam.

## Folder structure
```
weblume-company/
├── server.py              Dashboard server (built-in Python, no extra packages)
├── index.html             The dashboard page: 3D office + Home / Work / Progress / Team tabs
├── start.bat              Double-click to open the dashboard
├── requirements.txt
├── .env.example           Copy to .env (your settings and keys)
├── contacted.json         Businesses already contacted (Ziad never drafts for these)
├── knowledge/             brand/ (logo), taste.md (your taste, written up front), feedback.md, examples/approved/ (not uploaded)
├── weblume/
│   ├── config.py          Reads .env, builds the AI model (Gemini / Groq / Ollama)
│   ├── team.py            The 8 agents: name, role, goal, backstory
│   ├── tester.py          Tarek: screenshots in real Chrome + Gemini looks at them
│   ├── knowledge.py       Your 👍/👎 and approved examples, read before every design
│   ├── video/             Hassan: player.html (the frames) + the MP4 renderer
│   ├── company.py         Plans the work, runs the agents, saves files, live status, log
│   ├── rules.py           contacted.json + phone-number rules, cleaning AI answers
│   └── templates/         Karim's starting points (see below)
│       ├── cafe/          The Loopie design: scroll scenes from real video frames. Karim writes only the
│       │                  client's content (data.js); GUIDE.md there lists every field and photo
│       ├── clinic.html    Clinics and services: booking form that sends to WhatsApp, steps, FAQ
│       ├── shop.html      Stores and brands: product filters, cart that sends the order on WhatsApp
│       ├── motion.css/js  The animation kit, added to every site automatically
│       └── GUIDE.md       How Karim uses the kit (sent to him with the template)
├── tests/test_rules.py    Checks for the rules
└── output/
    ├── <client-name>/                    Final website (open it with the dashboard's button)
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
   Tarek (the tester) uses your installed Google Chrome or Edge, so there is no browser to download.
4. **Add your settings**:
   ```
   copy .env.example .env
   notepad .env
   ```
   Paste your free Gemini key after `GEMINI_API_KEY=` (get it at https://aistudio.google.com/apikey), save.
5. **Run**: double-click `start.bat` (or `.venv\Scripts\python server.py`).
   The dashboard opens at http://127.0.0.1:8501. Keep the black window open while you use it.

Check the rules any time: `.venv\Scripts\python tests\test_rules.py`

## Website templates
- **Cafés and restaurants → the Loopie design** (`weblume/templates/cafe/`): the approved Loopie site with its
  scroll scenes (coffee video frames, drinks dropping into a colored disc, a bean that roasts as you scroll).
  Karim fills only the client's content: name, tagline, brand colors, signature drinks, menu, WhatsApp, map,
  Arabic + English. The design can't break because he never touches it. It runs from the dashboard's
  **Open the website** button or GitHub Pages (scroll scenes don't run when the file is double-clicked).
- **Clinics/services and shops**: single pages Karim edits (`clinic.html`, `shop.html`), with the animation kit
  (`motion.css/js`) added by the code after him.
- To add a template: a folder like `cafe/` (index.html reading `window.CAFE`, assets, `GUIDE.md`,
  `example-data.js`) or a page with the two `<!--WEBLUME:...-->` markers; add its keywords to `KINDS`.

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
  Its free limits are small for long websites; use it for Ziad/Adam, Gemini for websites.
- **Bytez**: `LLM_PROVIDER=bytez`, `BYTEZ_API_KEY`, and `LLM_MODEL` set to a model id from your Bytez account.
- **Ollama (your laptop, offline, free)**: `LLM_PROVIDER=ollama`. Install Ollama from https://ollama.com, then:
  ```
  ollama pull qwen2.5:7b
  ```
  Keep it 7B–8B on the RTX 4060 8 GB (`qwen2.5:7b`, `llama3.1:8b`, or your own `weblume` model via
  `LLM_MODEL=weblume`). Give Ollama more memory for long prompts: Windows search → "environment variables" →
  New user variable `OLLAMA_CONTEXT_LENGTH` = `16384`, then restart Ollama. Small local models write weaker
  websites and sometimes break the JSON Layla/Ziad must return; the app then falls back safely (Layla) or
  tells you to run again (Ziad).

## Videos (Hassan)
Free mode only: `weblume/video/player.html` draws each frame, your Chrome captures it (Playwright) and ffmpeg
(`imageio-ffmpeg`, installed with the requirements) writes a 1080×1920 MP4 at 24 fps with no sound. Sites are
filmed scrolling first, then shown inside the mockups. A 20-second video takes about a minute to render.
Hassan can also add **AI photo scenes** (free, from Pollinations, no key): he writes what the photo shows
and the code fetches it and shows it full screen with a slow zoom and a caption. If a photo fails, the scene
becomes a text scene. Paid AI clips (Higgsfield / Runway / Kling) are not connected.

## When Gemini says "quota"
The free tier allows about 20 requests per day per model, and a website run uses many. When a model is busy or
out of quota the team switches to the next one, and to Groq (`openai/gpt-oss-120b`) last if `GROQ_API_KEY` is
set; if all of them are out, the run stops with a clear message
(it resets in about a day). Switch `LLM_PROVIDER` to `groq` or `ollama` in `.env` to keep working. A model that
doesn't answer within 2 minutes counts as busy (`LLM_CALL_TIMEOUT`).

## Troubleshooting
| Problem | Fix |
|---|---|
| `GEMINI_API_KEY is empty` | Put the key in `.env` (not `.env.example`) and restart |
| `429` / rate limit | Free tier limit. Wait a minute, or lower `MAX_REQUESTS_PER_MINUTE` in `.env` |
| `start.bat` says run setup first | Do steps 1–3 above |
| Ollama: connection refused | Open the Ollama app (it must be running) |
| Website file looks cut off | Use Gemini for websites; small local models stop early |

Not included: sending messages (you send them yourself), real Google Maps search (paste the names you find).
