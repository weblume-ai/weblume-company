# Café template (the Loopie design) — what Karim writes

The page design, scroll scenes and animations are finished. You only write the client's content as ONE JSON
object (no comments, no trailing commas). The code turns it into `data.js`. Follow the example's shape exactly.

Fields (Arabic first, English inside `en`):
- `name` (full name), `word` (one short word shown huge on screen: the brand word), `nameEn`
- `tagline` (6 words max, Egyptian Arabic, the hero headline), `lede` (one sentence: what + where)
- `about`, `invite` (short sign-off line), `together` (one short line shown big on the colored band), `hashtag` (optional)
- `colors`: `{"ink": "#…", "accent": "#…", "muted": "#…"}` from the client's brand. `ink` is the dark page
  color, `accent` the brand color for buttons and the band. Default to the example's if the brand is unknown.
- `currency` (e.g. "ج.م" or "ر.س"), `whatsapp` (digits with country code), `instagram`, `tiktok` (usernames,
  only if given), `mapsQuery` (name + street + city), `address`
- `hours`: `"24h"`, or an object with keys "0".."6" (0 = Sunday) each `{"open":"09:00","close":"01:00"}` or
  `"closed"`. Leave it out if unknown.
- `drinks`: 3 to 5 signature items, each `{"mood","name","desc","img","ratio","s","bg","disc","fg"}`. `mood` is
  a feeling in 1–2 words ("مستعجل", "جو هادي"). Use ONLY these cut-out images (keep their ratio and s):
  - `assets/img/drink-esp.webp` ratio "800/550" s .62 — espresso cup
  - `assets/img/drink-amer.webp` ratio "622/1011" s 1 — iced black coffee
  - `assets/img/drink-capp.webp` ratio "1070/1000" s .72 — latte / cappuccino cup
  - `assets/img/drink-tall.webp` ratio "440/1120" s 1.12 — tall iced milky drink
  - `assets/img/drink-green.webp` ratio "630/1060" s 1 — green / fruity cold drink
  `bg` is the scene color, `disc` the circle behind the drink, `fg` the text color: use the brand colors.
- `menu`: categories `{"name","img","alt","items":[{"name","desc","price"}]}`. Category photos to use:
  `assets/img/menu-coffee.webp` (latte art), `menu-drip.webp` (pour-over), `menu-matcha.webp`,
  `menu-dessert.webp` (brownies), or the drink cut-outs above with `"fit":"contain"`. `price` is a number from
  the request/spec; if prices are unknown use `""` (the page then hides the price). Never invent prices.
- `menuNote` (optional), `order` (link to Talabat/HungerStation if given)
- `aboutPhoto`, `visitPhoto`: `{"src","alt"}`; `place`: 3–4 `{"src","alt"}`. Mood photos available:
  `assets/img/mood-yellow.webp` (yellow cushions), `mood-tile.webp`, `mood-chair.webp`, `mood-stools.webp`,
  `mood-hall.webp` (big bright hall), `mood-cup.webp` (cup on the bar, warm light). If the request gives real
  photo URLs of the client, use those instead.
- `demo`: true (shows "a preview by Weblume" until the client approves)
- `en`: the same text fields translated (name, word, tagline, lede, address, about, invite, together, drinks
  [mood,name,desc], menuNote, menu [name, alt, items [name, desc]], aboutPhoto/visitPhoto/place alt)

Never invent ratings, reviews, years or customer counts (there is no field for them on purpose).
