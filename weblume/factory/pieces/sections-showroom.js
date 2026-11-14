/* Pieces written by Weblume after design ideas in screen recordings Asser shared (product showrooms: jars orbiting a
   shape, a colour chapter per product, a scroll-told coffee story, numbers counting up beside a product). Original
   vanilla code, the ideas only: no code, images or brands taken. RTL, phones, reduced motion respected. */
(function (P) {
  var E = function (s) { return SITEKIT.esc(s); };
  var pad = function (n) { return (n < 10 ? "0" : "") + n; };
  var goods = function (S, max) { // cut-out products first, then dish photos
    var a = (S.showcase || []).filter(function (s) { return s.cut; }).map(function (s) { return {img: s.cut, name: s.name, desc: s.desc, price: s.price, tone: s.tone, ink: s.ink, cut: 1}; });
    if (a.length < 3) {
      a = [];
      (S.menu || []).forEach(function (c) { (c.items || []).forEach(function (i) { if (i.img) a.push({img: i.img, name: i.name, desc: i.desc, price: i.price}); }); });
    }
    return a.slice(0, max || 6);
  };
  var order = function (t, it) { return SITEKIT.wa((t.lang === "en" ? "I'd like: " : "عايز أطلب: ") + it.name); };
  var orderBtn = function (t, it, cls) {
    return '<a class="btn ' + (cls || "a") + '" href="' + order(t, it) + '" target="_blank" rel="noopener noreferrer">' + (it.price ? E(it.price) + " " + E(t.cur) + " · " : "") + E(t.order) + "</a>";
  };
  var progress = function (sec) { var r = sec.getBoundingClientRect(), span = sec.offsetHeight - innerHeight; return span > 0 ? SITEKIT.clamp(-r.top / span) : 0; };
  var onScroll = function (fn) { var q = false; addEventListener("scroll", function () { if (!q) { q = true; requestAnimationFrame(function () { q = false; fn(); }); } }, {passive: true}); addEventListener("resize", fn); fn(); };

  /* hero-orbit — the products orbit a soft shape of the brand colour on a tilted ring; the front one is big and named,
     the far ones small and soft; a circle of the place's name turns slowly behind. Drag or tap to bring one forward. */
  P["hero-orbit"] = {
    css: ".hor{position:relative;height:calc(100svh - var(--nav));min-height:560px;overflow:hidden;background:var(--paper);color:var(--ink);display:grid;grid-template-rows:auto minmax(0,1fr) auto;padding:clamp(18px,3vw,36px) var(--gut)}" +
      ".hor h1{font-size:clamp(28px,3.6vw,56px);line-height:1.1;margin:0;max-width:14em;position:relative;z-index:30}" +
      ".hor .stage{position:relative;min-height:0;touch-action:pan-y;cursor:grab}" +
      ".hor .blob{position:absolute;left:50%;top:50%;height:min(78%,62vw);aspect-ratio:1.15;translate:-50% -50%;background:var(--accent);border-radius:46% 54% 42% 58%/52% 44% 56% 48%;animation:horBlob 14s ease-in-out infinite alternate}" +
      "@keyframes horBlob{to{border-radius:58% 42% 55% 45%/44% 58% 42% 56%;rotate:8deg}}" +
      ".hor .ringtx{position:absolute;left:50%;top:50%;height:min(104%,84vw);aspect-ratio:1;translate:-50% -50%;animation:horSpin 40s linear infinite;pointer-events:none}" +
      ".hor .ringtx text{font:800 11px var(--display);letter-spacing:.3em;fill:var(--ink);opacity:.75}@keyframes horSpin{to{rotate:360deg}}" +
      ".hor .it{position:absolute;left:50%;top:50%;width:clamp(150px,21vw,300px);aspect-ratio:3/4;margin:calc(clamp(150px,21vw,300px)*-.66) 0 0 calc(clamp(150px,21vw,300px)/-2);transition:filter .4s,opacity .4s}" +
      ".hor .it img{width:100%;height:100%;object-fit:cover;border-radius:var(--r-card);box-shadow:0 26px 40px #0004}.hor .it.cut img{object-fit:contain;border-radius:0;box-shadow:none;filter:drop-shadow(0 26px 30px #0005)}" +
      ".hor .foot{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:end;gap:14px;position:relative;z-index:30}" +
      ".hor .cap b{display:block;font:800 clamp(22px,2.6vw,38px)/1.1 var(--display)}.hor .cap small{color:var(--muted)}" +
      "@media (max-width:700px){.hor .blob{height:min(66%,92vw)}.hor .ringtx{height:min(92%,124vw)}}" +
      "@media (prefers-reduced-motion:reduce){.hor .blob,.hor .ringtx{animation:none}}",
    render: function (S, t) {
      var list = goods(S, 6);
      if (list.length < 3) return "";
      var word = E(S.word || S.name), ring = (word + " • ").repeat(6);
      return '<section class="hor" id="top"><h1>' + (S.heroLines && S.heroLines.length ? S.heroLines : [S.tagline || S.name]).map(E).join("<br>") + "</h1>" +
        '<div class="stage"><div class="blob" aria-hidden="true"></div><svg class="ringtx" viewBox="0 0 200 200" aria-hidden="true"><defs><path id="horP" d="M100,100 m-82,0 a82,82 0 1,1 164,0 a82,82 0 1,1 -164,0"/></defs><text direction="ltr"><textPath href="#horP">' + ring + "</textPath></text></svg>" +
        list.map(function (it) { return '<div class="it' + (it.cut ? " cut" : "") + '"><img src="' + E(it.img) + '" alt="' + E(it.name) + '"></div>'; }).join("") +
        '</div><div class="foot"><div class="cap" aria-live="polite"><b></b><small></small></div><span class="act"></span></div></section>';
    },
    init: function (S, t) {
      var sec = document.querySelector(".hor"); if (!sec) return;
      var list = goods(S, 6), its = sec.querySelectorAll(".it"), stage = sec.querySelector(".stage"), N = its.length;
      var rot = 0, target = 0, front = -1, drag = null, rtl = document.documentElement.dir === "rtl" ? -1 : 1;
      var place = function () {
        var w = stage.clientWidth, Rx = Math.min(w * .4, 460), Ry = Math.min(stage.clientHeight * .2, 110), best = -2, bi = 0;
        [].forEach.call(its, function (el, i) {
          var a = rot + i * 2 * Math.PI / N, depth = Math.sin(a); // 1 = in front
          el.style.transform = "translate(" + (Math.cos(a) * Rx * rtl).toFixed(1) + "px," + (depth * Ry).toFixed(1) + "px) scale(" + (.55 + .45 * (depth + 1) / 2).toFixed(3) + ")";
          el.style.zIndex = Math.round(10 + depth * 10);
          el.style.filter = depth < -.2 ? "blur(2px)" : "none"; el.style.opacity = (.55 + .45 * (depth + 1) / 2).toFixed(2);
          if (depth > best) { best = depth; bi = i; }
        });
        if (bi !== front) {
          front = bi; var it = list[bi];
          sec.querySelector(".cap b").textContent = it.name; sec.querySelector(".cap small").textContent = it.desc || "";
          sec.querySelector(".act").innerHTML = orderBtn(t, it);
        }
      };
      var bring = function (i) { var want = Math.PI / 2 - i * 2 * Math.PI / N; target = rot + (((want - rot) % (2 * Math.PI)) + 3 * Math.PI) % (2 * Math.PI) - Math.PI; };
      [].forEach.call(its, function (el, i) { el.addEventListener("click", function () { bring(i); }); });
      stage.addEventListener("pointerdown", function (e) { drag = {x: e.clientX, r: target}; });
      addEventListener("pointermove", function (e) { if (drag) target = drag.r + (e.clientX - drag.x) / 220 * rtl; });
      addEventListener("pointerup", function () { if (drag) { drag = null; bring(front); } });
      var last = performance.now();
      (function tick(now) {
        var dt = Math.min(.05, (now - last) / 1000); last = now;
        if (!SITEKIT.reduce && !drag) target += dt * .25; // a slow turn on its own
        rot += (target - rot) * Math.min(1, dt * 6);
        place(); requestAnimationFrame(tick);
      })(last);
      addEventListener("resize", place); place();
    }
  };

  /* band-chapters — one full screen per signature item, each in its own colour: its name huge behind it, the item
     floating in front, its description and order button below; scrolling moves from chapter to chapter. */
  P["band-chapters"] = {
    css: ".bch{position:relative;background:var(--ink)}.bch .stage{position:sticky;top:0;height:100svh;overflow:hidden;background:var(--bg,var(--accent));color:var(--fg,var(--on-accent));transition:background-color .7s cubic-bezier(.4,0,.2,1),color .7s}" +
      ".bch .word{position:absolute;inset-inline:0;top:50%;translate:0 -58%;text-align:center;font:900 clamp(80px,19vw,300px)/1 var(--display);white-space:nowrap;opacity:.9;pointer-events:none}" +
      ".bch .ch{position:absolute;inset:0;display:grid;place-items:center;opacity:0;visibility:hidden;transition:opacity .6s,visibility .6s}.bch .ch.on{opacity:1;visibility:visible}" +
      ".bch .ch img{width:min(46vh,58vw);aspect-ratio:1;object-fit:cover;border-radius:50%;box-shadow:0 40px 60px #0005;transform:translateY(60px) scale(.8) rotate(-12deg);transition:transform .9s cubic-bezier(.2,.8,.2,1)}" +
      ".bch .ch.cut img{object-fit:contain;border-radius:0;box-shadow:none;filter:drop-shadow(0 40px 40px #0006)}.bch .ch.on img{transform:none}" +
      ".bch .say{position:absolute;inset-inline:var(--gut);bottom:clamp(20px,6vh,56px);display:flex;flex-wrap:wrap;justify-content:space-between;align-items:end;gap:12px;z-index:3}" +
      ".bch .say b{display:block;font:800 clamp(22px,2.4vw,36px)/1.1 var(--display)}.bch .say p{margin:6px 0 0;opacity:.85;max-width:34ch}" +
      ".bch .dots{position:absolute;inset-inline-end:var(--gut);top:50%;translate:0 -50%;display:grid;gap:8px;z-index:3}.bch .dots i{width:8px;height:8px;border-radius:50%;background:currentColor;opacity:.3}.bch .dots i.on{opacity:1;height:24px;border-radius:8px}" +
      "@media (prefers-reduced-motion:reduce){.bch .stage,.bch .ch,.bch .ch img{transition:none}}",
    render: function (S, t) {
      var list = goods(S, 5);
      if (list.length < 3) return "";
      var tones = ["var(--accent)", "var(--surface)", "color-mix(in srgb,var(--accent) 55%,var(--paper))", "color-mix(in srgb,var(--accent) 60%,var(--ink))", "var(--paper)"];
      var inks = ["var(--on-accent)", "var(--paper)", "var(--ink)", "var(--paper)", "var(--ink)"];
      return '<section class="bch" style="height:' + (list.length * 85 + 15) + 'svh" aria-label="' + E(t.lang === "en" ? "Our signature" : "أشهر حاجاتنا") + '"><div class="stage"><div class="word" aria-hidden="true"></div>' +
        list.map(function (it, i) {
          return '<div class="ch' + (it.cut ? " cut" : "") + (i ? "" : " on") + '" data-bg="' + E(it.tone || tones[i % 5]) + '" data-fg="' + E(it.ink || inks[i % 5]) + '"><img src="' + E(it.img) + '" alt="' + E(it.name) + '" loading="lazy"></div>';
        }).join("") + '<div class="say"><div><b></b><p></p></div><span class="act"></span></div><div class="dots" aria-hidden="true">' + list.map(function (x, i) { return "<i" + (i ? "" : ' class="on"') + "></i>"; }).join("") + "</div></div></section>";
    },
    init: function (S, t) {
      var sec = document.querySelector(".bch"); if (!sec) return;
      var list = goods(S, 5), chs = sec.querySelectorAll(".ch"), dots = sec.querySelectorAll(".dots i"), stage = sec.querySelector(".stage"), at = -1;
      var show = function (i) {
        if (i === at) return; at = i; var it = list[i], ch = chs[i];
        [].forEach.call(chs, function (c, k) { c.classList.toggle("on", k === i); });
        [].forEach.call(dots, function (d, k) { d.classList.toggle("on", k === i); });
        stage.style.setProperty("--bg", ch.dataset.bg); stage.style.setProperty("--fg", ch.dataset.fg);
        sec.querySelector(".word").textContent = it.name; sec.querySelector(".say b").textContent = it.name;
        sec.querySelector(".say p").textContent = it.desc || ""; sec.querySelector(".act").innerHTML = orderBtn(t, it, "w");
      };
      onScroll(function () { show(Math.min(list.length - 1, Math.floor(progress(sec) * list.length))); });
      show(0);
    }
  };

  /* how-film — the place's craft told in chapters while the screen stays put: a big photo slowly zooming, a giant
     short title (the scene captions), the chapter number; scrolling moves to the next chapter. */
  P["how-film"] = {
    css: ".hfm{position:relative;background:var(--ink);color:#fff}.hfm .stage{position:sticky;top:0;height:100svh;overflow:hidden}" +
      ".hfm .sh{position:absolute;inset:0;opacity:0;transition:opacity .9s ease}.hfm .sh.on{opacity:1}" +
      ".hfm .sh img{width:100%;height:100%;object-fit:cover;transform:scale(1.18);transition:transform 6s cubic-bezier(.2,.7,.2,1)}.hfm .sh.on img{transform:scale(1.02)}" +
      ".hfm .stage:after{content:'';position:absolute;inset:0;background:linear-gradient(#0007,#0002 40%,#0008)}" +
      ".hfm .tt{position:absolute;inset-inline:var(--gut);bottom:clamp(40px,12vh,120px);z-index:2;font:900 clamp(48px,10vw,160px)/.95 var(--display);text-shadow:0 10px 40px #0007}" +
      ".hfm .tt span{display:inline-block;opacity:0;transform:translateY(40%);transition:opacity .6s,transform .8s cubic-bezier(.2,.8,.2,1);transition-delay:calc(var(--w)*90ms)}.hfm .tt.on span{opacity:1;transform:none}" +
      ".hfm .no{position:absolute;top:clamp(20px,6vh,60px);inset-inline-start:var(--gut);z-index:2;font:700 var(--small)/1 var(--text);letter-spacing:.25em;color:var(--accent)}" +
      ".hfm .bar{position:absolute;inset-inline:var(--gut);bottom:clamp(20px,5vh,48px);height:2px;background:#fff3;z-index:2}.hfm .bar i{position:absolute;inset:0;background:var(--accent);transform-origin:right;transform:scaleX(var(--p,0))}" +
      "@media (prefers-reduced-motion:reduce){.hfm .sh,.hfm .sh img,.hfm .tt span{transition:none}}",
    render: function (S, t) {
      var caps = (S.caps && S.caps.length >= 3 ? S.caps : S.features || []).slice(0, 4), g = (S.media && S.media.gallery) || [];
      if (caps.length < 3 || g.length < 3) return "";
      return '<section class="hfm" id="how" style="height:' + (caps.length * 90 + 10) + 'svh"><div class="stage">' +
        caps.map(function (c, i) { var p = g[i % g.length]; return '<div class="sh' + (i ? "" : " on") + '"><img src="' + E(p.src) + '" alt="' + E(p.alt || c) + '" loading="lazy"></div>'; }).join("") +
        '<div class="no" dir="ltr"></div>' + caps.map(function (c, i) {
          return '<h2 class="tt' + (i ? "" : " on") + '"' + (i ? ' aria-hidden="true"' : "") + ">" + String(c).split(/\s+/).map(function (w, k) { return '<span style="--w:' + k + '">' + E(w) + "</span>"; }).join(" ") + "</h2>";
        }).join("") + '<div class="bar"><i></i></div></div></section>';
    },
    init: function () {
      var sec = document.querySelector(".hfm"); if (!sec) return;
      var sh = sec.querySelectorAll(".sh"), tt = sec.querySelectorAll(".tt"), N = sh.length, at = -1, bar = sec.querySelector(".bar");
      onScroll(function () {
        var p = progress(sec), i = Math.min(N - 1, Math.floor(p * N));
        bar.style.setProperty("--p", p.toFixed(3));
        if (i === at) return; at = i;
        [].forEach.call(sh, function (s, k) { s.classList.toggle("on", k === i); });
        [].forEach.call(tt, function (s, k) { s.classList.toggle("on", k === i); s.setAttribute("aria-hidden", k === i ? "false" : "true"); });
        sec.querySelector(".no").textContent = pad(i + 1) + " / " + pad(N);
      });
    }
  };

  /* features-stats — the place's real numbers (from its strengths: "24 ساعة", "15 سنة", "3 فروع") count up big as
     they come into view, each with its short line, beside a photo of the place that turns slowly. Only true numbers. */
  P["features-stats"] = {
    css: ".fst{position:relative;overflow:hidden;background:var(--ink);color:var(--paper);padding:clamp(80px,11vw,160px) var(--gut);display:grid;gap:40px;align-items:center}" +
      ".fst .nums{display:grid;gap:clamp(24px,4vw,48px)}.fst .n b{display:block;font:900 clamp(64px,9vw,150px)/.9 var(--display);font-variant-numeric:tabular-nums;color:var(--accent)}" +
      ".fst .n span{display:block;font:700 clamp(18px,1.8vw,26px)/1.3 var(--display);margin-top:8px;max-width:16em}" +
      ".fst figure{margin:0;aspect-ratio:4/5;border-radius:var(--r-card);overflow:hidden;background:var(--surface);max-width:460px;justify-self:center;width:100%}" +
      ".fst figure img{width:100%;height:100%;object-fit:cover;animation:fstTurn 18s ease-in-out infinite alternate}@keyframes fstTurn{to{transform:scale(1.12) rotate(3deg)}}" +
      "@media (min-width:860px){.fst{grid-template-columns:1.2fr 1fr}}@media (prefers-reduced-motion:reduce){.fst figure img{animation:none}}",
    _nums: function (S) {
      var out = [];
      (S.features || []).forEach(function (f) {
        var s = String(f).replace(/[٠-٩]/g, function (d) { return "٠١٢٣٤٥٦٧٨٩".indexOf(d); }), m = s.match(/(\d+(?:[.,]\d+)?)/);
        if (m) out.push({n: m[1], rest: String(f)}); // the whole true sentence stays under its number
      });
      return out.slice(0, 3);
    },
    render: function (S, t) {
      var nums = P["features-stats"]._nums(S), m = S.media || {}, ph = (m.gallery && m.gallery[0] && m.gallery[0].src) || m.heroImg;
      if (nums.length < 2) return ""; // only real numbers count up: two or more strengths must carry one
      return '<section class="fst" id="why"><div class="nums">' + nums.map(function (x, i) {
        return '<div class="n rise" style="--i:' + i + '"><b data-n="' + E(x.n) + '">0</b><span>' + E(x.rest) + "</span></div>";
      }).join("") + "</div>" + (ph ? '<figure><img src="' + E(ph) + '" alt="' + E(S.name) + '" loading="lazy"></figure>' : "") + "</section>";
    },
    init: function () {
      var sec = document.querySelector(".fst"); if (!sec) return;
      var bs = sec.querySelectorAll(".n b"), done = false;
      var run = function () {
        if (done) return; done = true;
        [].forEach.call(bs, function (b) {
          var end = parseFloat(String(b.dataset.n).replace(",", ".")), dec = /[.,]/.test(b.dataset.n) ? 1 : 0, t0 = performance.now();
          if (SITEKIT.reduce) return (b.textContent = b.dataset.n);
          (function step(now) { var k = Math.min(1, (now - t0) / 1600), e = 1 - Math.pow(1 - k, 3); b.textContent = (end * e).toFixed(dec); if (k < 1) requestAnimationFrame(step); else b.textContent = b.dataset.n; })(t0);
        });
      };
      if (!("IntersectionObserver" in window)) return run();
      new IntersectionObserver(function (es, o) { if (es[0].isIntersecting) { run(); o.disconnect(); } }, {threshold: .35}).observe(sec);
    }
  };
})(window.PIECES = window.PIECES || {});
