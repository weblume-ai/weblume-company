# Skill: motion that feels premium (after GreenSock's official GSAP skills, MIT, github.com/greensock/gsap-skills)
Asser's rule: every section moves. Motion tells the story of the page; it never just decorates.
- One opening moment: the page arrives (the brand word rises, a photo window opens, lines draw, a short loader counts
  to 100). Under 2 seconds, never blocks reading twice in one visit.
- Scroll tells the story: sections rise as they enter (staggered 60-120 ms per item), big headings drift sideways,
  photos uncover and drift slower than the page (parallax), a scroll-played video for the place's craft.
- Numbers count up when seen (orders, years open only if TRUE, branches), never invented to have something to count.
- Ease: power3.out / cubic-bezier(.2,.7,.2,1) for entrances, linear only for scroll-linked and marquees, back.out
  only for small playful things. Durations 0.5-0.9 s; long lists stagger, never all at once.
- Animate transform and opacity (and clip-path for reveals); never width, height, top or left (jank).
- Arabic text animates word by word or line by line, never letter by letter (letters must stay joined). Latin
  words may split by letter.
- Respect prefers-reduced-motion: show everything at once, keep the layout. (In GSAP: gsap.matchMedia().)
- Hover on desktop only: photos zoom slightly, buttons lean toward the pointer; on phones the same moment plays on
  scroll or tap.
- In code with GSAP: register plugins once, defaults in one place (gsap.defaults), timelines for sequences,
  ScrollTrigger with scrub for scroll-linked motion and toggleActions for entrances, kill triggers when a section is
  removed, pin only when the section is short enough to stay readable on a phone.
- Check: does every section move? Does anything move without a reason? Does it still read with motion turned off?
