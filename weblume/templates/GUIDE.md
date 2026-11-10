# Weblume motion kit — how to use it

The animation engine (CSS + JS) is injected automatically where these two markers are. Keep both markers exactly:
`<!--WEBLUME:MOTION_CSS-->` inside `<head>`, `<!--WEBLUME:MOTION_JS-->` just before `</body>`.
Never write your own animation library; use these classes on any element:

| Use | Markup |
|---|---|
| Fade/slide in on scroll | `class="reveal"` (+ `from-left`, `from-right` or `zoom`); delay with `style="--i:2"` |
| Children appear one after another | `data-stagger` on the parent |
| Big heading rising word by word | `class="split"` on an h1/h2 with plain text only |
| Endless moving strip | `<div class="marquee"><div>…items…</div></div>` (`--speed:20s`) |
| 3D tilt card | `class="tilt"`; a child with `tilt-pop` floats above it |
| Button that follows the cursor | `class="magnetic"` |
| Light sweep on hover | `class="shine"` |
| Number that counts up | `<b data-count="250" data-suffix="+">0</b>` (decimals ok: `4.8`) |
| Parallax | `data-speed="-0.05"` (small values, -0.1 to 0.1) |
| Floating badge | `class="float"` |
| Cursor glow | `data-glow` on `<body>` |
| Mobile menu | button `data-menu-toggle`, nav `data-menu` |
| Arabic/English | Arabic in the markup, English in `data-en="…"` on elements with plain text only (no child tags); button `data-lang-toggle`; inputs `data-en-placeholder` |
| WhatsApp | client's number in `<body data-wa="2010…">`; any link/button `data-wa-msg="message"` (+ `data-wa-from="#id1,#id2"` to add form fields) |

Rules:
- Change colors only through the `:root` variables at the top of the template (use the client's brand colors).
- Every `.ph` needs `data-photo="…"`: an ENGLISH description of the exact photo for this business (it becomes a stand-in photo automatically).
- `.ph` blocks are photo placeholders: with real image URLs use `<img src alt loading="lazy">`; otherwise keep `.ph` and set `data-label` to the photo the client should send.
- Keep sections the client needs, delete the rest, add new ones with the same classes. Keep the template's own small `<script>` (tabs, filters, cart).
- No fake reviews, numbers or awards: remove counters you have no real numbers for.
- The page must stay one file that works with a double-click.
