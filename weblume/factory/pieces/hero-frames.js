/* hero-frames — from Loopie: the place's own footage as WebP frames on a canvas, played by the scroll (pinned).
   data: media.frames = {d: "assets/frames-d/", m: "assets/frames-m/", n: 120}; heroLines, lede, caps (optional). */
(window.PIECES = window.PIECES || {})["hero-frames"] = {
  css: ".hf{height:420vh}.hf .stage{background:var(--ink)}.hf canvas{position:absolute;inset:0;width:100%;height:100%}" +
    ".hf .scrim{position:absolute;inset:0;background:#000;opacity:.48}.hf .hero{text-shadow:0 2px 24px #000a}" +
    ".hf .hero{position:absolute;inset-inline:var(--gut);top:calc(var(--nav) + 8vh);max-width:min(56vw,860px);z-index:2}" +
    ".hf h1{font-size:clamp(38px,5.4vw,96px)}.hf h1 span{display:block}" +
    ".hf .hero p{font-size:var(--lead);line-height:1.4;margin-top:clamp(18px,3vh,32px);max-width:26em}" +
    ".hf .acts{display:flex;flex-wrap:wrap;align-items:center;gap:18px;margin-top:clamp(18px,3vh,32px)}.hf small{color:var(--muted)}" +
    ".hf .cap{position:absolute;inset-inline:var(--gut);bottom:clamp(24px,7vh,64px);font:800 var(--giant)/1.05 var(--display);z-index:2;opacity:0;transition:opacity .4s}" +
    "@media (max-width:859px){.hf .hero{max-width:none;top:calc(var(--nav) + 3vh)}.hf h1{font-size:clamp(34px,10vw,64px)}.hf .hero p{font-size:var(--body)}.hf small{display:none}}",
  render: function (S, t) {
    var K = SITEKIT, lines = S.heroLines || [S.tagline || S.name];
    return '<section class="pin hf" id="top"><div class="stage"><canvas aria-hidden="true"></canvas><div class="scrim"></div>' +
      '<div class="hero"><h1>' + lines.map(function (l) { return "<span>" + K.esc(l) + "</span>"; }).join("") + "</h1><p>" + K.esc(S.lede) + "</p>" +
      '<div class="acts"><a class="btn a" href="#menu">' + t.see + "</a><small>" + t.hint + "</small></div></div>" +
      (S.caps || []).map(function (c, i) { return '<div class="cap" aria-hidden="true" data-i="' + i + '">' + K.esc(c) + "</div>"; }).join("") + "</div></section>";
  },
  init: function (S) {
    var K = SITEKIT, sec = document.querySelector(".hf"), cv = sec.querySelector("canvas"), g = cv.getContext("2d");
    var F = (S.media || {}).frames || {}, portrait = innerWidth < innerHeight, base = portrait ? F.m || F.d : F.d || F.m, n = F.n || 0;
    var img = [], hero = sec.querySelector(".hero"), caps = sec.querySelectorAll(".cap"), shown = -1;
    if (!base || !n) { if ((S.media || {}).heroImg) sec.querySelector(".stage").style.background = "url('" + S.media.heroImg + "') center/cover"; return; }
    /* every 6th frame first so the whole scene can be scrubbed early, then the rest */
    var order = [];
    for (var i = 0; i < n; i += 6) order.push(i);
    for (i = 0; i < n; i++) if (i % 6) order.push(i);
    order.forEach(function (k) { var im = new Image(); im.decoding = "async"; im.onload = function () { if (Math.abs(k - shown) < 4) draw(true); }; im.src = base + String(k + 1).padStart(3, "0") + ".webp"; img[k] = im; });
    function draw(force) {
      var p = K.progress(sec), at = Math.round(p * (n - 1)), im = null;
      for (var d = 0; d < n && !im; d++) { var a = img[at - d], b = img[at + d]; im = a && a.complete && a.naturalWidth ? a : b && b.complete && b.naturalWidth ? b : null; }
      hero.style.opacity = Math.max(0, 1 - p * 5); hero.style.visibility = p > .2 ? "hidden" : "visible";
      [].forEach.call(caps, function (c, j) { var a0 = .25 + j * (.7 / caps.length); c.style.opacity = p > a0 && p < a0 + .7 / caps.length - .02 ? 1 : 0; });
      if (!im || (at === shown && !force)) return;
      shown = at;
      var dpr = Math.min(devicePixelRatio || 1, 2), w = cv.clientWidth * dpr, h = cv.clientHeight * dpr;
      if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
      var s = Math.max(w / im.naturalWidth, h / im.naturalHeight), iw = im.naturalWidth * s, ih = im.naturalHeight * s;
      g.drawImage(im, (w - iw) / 2, (h - ih) / 2, iw, ih);
    }
    var queued = false;
    addEventListener("scroll", function () { if (!queued) { queued = true; requestAnimationFrame(function () { queued = false; draw(); }); } }, {passive: true});
    addEventListener("resize", function () { draw(true); });
    draw(true);
  }
};
