/* hero-showcase — after the owner's reference video (product hero with a flat colour per flavour, the flavour's name huge
   and faded behind it, the product cut out and floating, small pieces flying around, arrows to switch).
   data: showcase = [{name, desc, price, cut: "assets/cut/1.png", tone: "#e4447a", ink: "#fff"}] (made by media.py from photos). */
(window.PIECES = window.PIECES || {})["hero-showcase"] = {
  css: ".hsc{position:relative;height:calc(100svh - var(--nav));min-height:560px;overflow:hidden;background:var(--tone,#e4447a);color:var(--tink,#fff);transition:background .8s ease}" +
    ".hsc .word{position:absolute;inset-inline:0;top:50%;transform:translateY(-58%);text-align:center;font:800 clamp(90px,24vw,400px)/1 var(--display);white-space:nowrap;opacity:.16;pointer-events:none;transition:opacity .5s}" +
    ".hsc .slide{position:absolute;inset:0;display:grid;place-items:center;opacity:0;visibility:hidden;transition:opacity .6s,visibility .6s}.hsc .slide.on{opacity:1;visibility:visible}" +
    ".hsc .prod{width:min(46vh,62vw);aspect-ratio:1;object-fit:contain;filter:drop-shadow(0 30px 40px #0005);transform:translateY(40px) scale(.9) rotate(-6deg);transition:transform .9s cubic-bezier(.2,.7,.2,1)}" +
    ".hsc .slide.on .prod{transform:none;animation:hscFloat 5s ease-in-out .9s infinite}" +
    "@keyframes hscFloat{50%{transform:translateY(-14px) rotate(2deg)}}" +
    ".hsc .bit{position:absolute;width:clamp(44px,6vw,96px);aspect-ratio:1;object-fit:contain;opacity:0;filter:drop-shadow(0 10px 14px #0004) blur(.4px);transition:opacity .8s,transform 1.2s cubic-bezier(.2,.7,.2,1)}" +
    ".hsc .slide.on .bit{opacity:.9;animation:hscBit 7s ease-in-out infinite}" +
    "@keyframes hscBit{50%{translate:0 -18px;rotate:14deg}}" +
    ".hsc .info{position:absolute;inset-inline-start:var(--gut);bottom:clamp(20px,6vh,56px);max-width:min(34ch,80vw);z-index:3}" +
    ".hsc .info b{display:block;font:800 clamp(28px,3.4vw,52px)/1.1 var(--display)}.hsc .info p{margin:8px 0 14px;opacity:.85}" +
    ".hsc .ctrl{position:absolute;inset-inline-end:var(--gut);bottom:clamp(20px,6vh,56px);display:flex;align-items:center;gap:10px;z-index:3}" +
    ".hsc .ctrl button{width:52px;height:52px;border-radius:50%;border:2px solid currentColor;background:none;color:inherit;font-size:22px;cursor:pointer}" +
    ".hsc .dots{display:flex;gap:6px}.hsc .dots i{width:8px;height:8px;border-radius:50%;background:currentColor;opacity:.35}.hsc .dots i.on{opacity:1;width:22px;border-radius:8px}" +
    "@media (max-width:700px){.hsc .info{bottom:96px}.hsc .ctrl{inset-inline:var(--gut);justify-content:space-between}}" +
    "@media (prefers-reduced-motion:reduce){.hsc .slide.on .prod,.hsc .slide.on .bit{animation:none}}",
  render: function (S, t) {
    var E = SITEKIT.esc, list = S.showcase || [], spots = [[8, 18], [78, 14], [14, 70], [82, 66], [46, 8]];
    if (list.length < 2) return "";
    return '<section class="hsc" id="top" aria-roledescription="carousel" aria-label="' + E(S.name) + '" style="--tone:' + E(list[0].tone) + ";--tink:" + E(list[0].ink) +
      '"><div class="word" aria-hidden="true">' + E(list[0].name) + "</div>" + list.map(function (s, i) {
        var bits = list.filter(function (o, j) { return j !== i; }).concat(list).slice(0, 4);
        return '<div class="slide' + (i ? "" : " on") + '" role="group" aria-label="' + E(s.name) + '"><img class="prod" src="' + E(s.cut) + '" alt="' + E(s.name) + '">' +
          bits.map(function (b, k) { var p = spots[(k + i) % spots.length]; return '<img class="bit" src="' + E(b.cut) + '" alt="" aria-hidden="true" style="left:' + p[0] + "%;top:" + p[1] + "%;animation-delay:" + (-k * 1.3) + 's">'; }).join("") +
          '<div class="info"><b>' + E(s.name) + "</b>" + (s.desc ? "<p>" + E(s.desc) + "</p>" : "") +
          '<a class="btn w" href="' + SITEKIT.wa((t.lang === "en" ? "I'd like: " : "عايز أطلب: ") + s.name) + '" target="_blank" rel="noopener noreferrer">' + (s.price ? E(s.price) + t.cur + " · " : "") + t.order + "</a></div></div>";
      }).join("") + '<div class="ctrl"><button type="button" class="prev" aria-label="previous">‹</button><div class="dots">' + list.map(function (s, i) { return '<i class="' + (i ? "" : "on") + '"></i>'; }).join("") +
      '</div><button type="button" class="next" aria-label="next">›</button></div></section>';
  },
  init: function (S) {
    var sec = document.querySelector(".hsc"); if (!sec) return;
    var list = S.showcase, slides = sec.querySelectorAll(".slide"), dots = sec.querySelectorAll(".dots i"), word = sec.querySelector(".word"), at = 0, timer;
    var rtl = document.documentElement.dir === "rtl";
    function go(n) {
      at = (n + list.length) % list.length;
      [].forEach.call(slides, function (s, i) { s.classList.toggle("on", i === at); });
      [].forEach.call(dots, function (d, i) { d.classList.toggle("on", i === at); });
      sec.style.setProperty("--tone", list[at].tone); sec.style.setProperty("--tink", list[at].ink);
      word.style.opacity = 0; setTimeout(function () { word.textContent = list[at].name; word.style.opacity = ""; }, 250);
    }
    function auto() { clearInterval(timer); if (!SITEKIT.reduce) timer = setInterval(function () { go(at + 1); }, 5000); }
    sec.querySelector(".next").addEventListener("click", function () { go(at + (rtl ? -1 : 1)); auto(); });
    sec.querySelector(".prev").addEventListener("click", function () { go(at + (rtl ? 1 : -1)); auto(); });
    var x0 = null;
    sec.addEventListener("pointerdown", function (e) { x0 = e.clientX; });
    sec.addEventListener("pointerup", function (e) { if (x0 !== null && Math.abs(e.clientX - x0) > 50) { go(at + ((e.clientX < x0) !== rtl ? 1 : -1)); auto(); } x0 = null; });
    sec.addEventListener("mousemove", function (e) { // the pieces lean away from the pointer a little
      var dx = (e.clientX / innerWidth - .5) * 24, dy = (e.clientY / innerHeight - .5) * 24;
      [].forEach.call(slides[at].querySelectorAll(".bit"), function (b, k) { b.style.transform = "translate(" + dx * (k % 2 ? 1 : -1) + "px," + dy + "px)"; });
    });
    auto();
  }
};
