/* nav — from Loopie: sticky dark bar, brand, section links, WhatsApp, language switch, full-screen phone menu */
(window.PIECES = window.PIECES || {}).nav = {
  css: ".nav{position:sticky;top:0;z-index:20;height:var(--nav);display:flex;align-items:center;justify-content:space-between;gap:24px;padding-inline:var(--gut);background:var(--ink);color:var(--paper)}" +
    ".brand{display:flex;align-items:center;gap:10px;font:800 19px/1 var(--display)}.brand img{height:30px;width:auto}" +
    ".nav ul{display:none;gap:30px;font-weight:500}.nav a:hover,.nav button:hover{color:var(--accent)}.nav .end{display:flex;align-items:center;gap:18px}" +
    ".nav button{background:none;border:0;color:inherit;font:700 var(--body) var(--text);cursor:pointer;min-height:44px}" +
    "@media (min-width:860px){.nav ul{display:flex}.nav .mo{display:none}}@media (max-width:859px){.nav .wa{display:none}}" +
    ".mnav{position:fixed;inset:0;z-index:40;background:var(--ink);display:flex;flex-direction:column;justify-content:center;gap:6px;padding:72px var(--gut) 40px}" +
    ".mnav[hidden]{display:none}.mnav a{font:800 clamp(40px,12vw,64px)/1.35 var(--display)}" +
    ".mnav .x{position:absolute;top:14px;inset-inline-end:var(--gut);background:none;border:0;color:inherit;font:700 var(--body) var(--text);min-height:44px;cursor:pointer}",
  render: function (S, t) {
    var K = SITEKIT, links = [["#menu", t.menu, "menu"], ["#gallery", t.gallery, "gallery"], ["#visit", t.visit, "visit"]]
      .filter(function (l) { return (S.pieces || []).some(function (p) { return p.indexOf(l[2]) === 0; }); });
    var a = links.map(function (l) { return '<a href="' + l[0] + '">' + l[1] + "</a>"; }).join("");
    return '<header class="nav"><a class="brand" href="#top" aria-label="' + K.esc(S.name) + '">' + (S.logo ? '<img src="' + K.esc(S.logo) + '" alt="">' : "") +
      "<span>" + K.esc(S.word || S.name) + "</span></a><ul>" + a.replace(/<a/g, "<li><a").replace(/<\/a>/g, "</a></li>") + '</ul><div class="end">' +
      '<a class="wa" href="' + K.wa() + '" target="_blank" rel="noopener noreferrer">' + t.wa + "</a>" + (S.en ? "<button type=\"button\" data-lang></button>" : "") +
      '<button class="mo" type="button" aria-expanded="false" aria-controls="mnav">' + t.open + "</button></div></header>" +
      '<div class="mnav" id="mnav" hidden><button class="x" type="button">' + t.close + "</button>" + a +
      '<a href="' + K.wa() + '" target="_blank" rel="noopener noreferrer">' + t.wa + "</a></div>";
  },
  init: function () {
    var m = document.getElementById("mnav"), o = document.querySelector(".nav .mo");
    var set = function (v) { m.hidden = !v; o.setAttribute("aria-expanded", v); document.body.style.overflow = v ? "hidden" : ""; };
    o.addEventListener("click", function () { set(true); });
    m.addEventListener("click", function (e) { if (e.target.tagName === "A" || e.target.classList.contains("x")) set(false); });
    addEventListener("keydown", function (e) { if (e.key === "Escape") set(false); });
  }
};
