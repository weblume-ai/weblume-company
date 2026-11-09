# Skill: security for every site we ship
A static site still leaks or breaks if it's careless. Before a site is delivered:
1. No secrets in the page: no API keys, tokens, passwords, private emails or admin links in HTML/JS/data files.
   Firebase/Supabase web config is public by design, so the database rules must lock writes to the admin.
2. HTTPS only: every script, style, image and link uses https:// (http:// gets blocked as mixed content).
3. Links that open a new tab: target="_blank" always with rel="noopener noreferrer".
4. Scripts only from trusted CDNs (cdnjs, jsdelivr, unpkg, Google Fonts) with an exact version. No random hosts,
   no trackers, no copied "free widget" scripts.
5. Anything a visitor types is shown with textContent, never innerHTML. Forms validate input and never send it to
   an unknown server; WhatsApp/mailto only, to the client's own number/email.
6. Admin pages (menu editors): real sign-in (Firebase Auth / Supabase Auth) and server-side rules, never a password
   checked in JavaScript, never "security by a hidden URL".
7. Personal data: never the owner's phone number or location; only the client's public business details.
8. If a key was ever published by mistake: say so at once. It must be rotated; deleting it is not enough.
The code also scans every finished site (`weblume/security.py`) and fixes or reports what it finds.
Report problems as: the problem · how serious (high/medium/low) · the fix.
