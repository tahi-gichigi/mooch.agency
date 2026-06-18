# mooch.agency

The website for Mooch, a UX research and AI automation studio in London and Lisbon. A husband-and-wife team.

Live at [www.mooch.agency](https://www.mooch.agency).

## What's here

Static HTML, no build step. Every page is a standalone `.html`, served as-is on Vercel.

- **Pages.** The homepage, `ready.html` (an AI readiness self-audit), case studies (GOV.UK, Octant, British Airways, and more), and `404.html`.
- **Playthings.** Small tools we build to think out loud. `paulgraham.html` rewrites your writing in Paul Graham's voice and scores it against a profile built from 208 of his essays. The profile, scorer, and validation live in `pg-rewriter/`.
- **Design system.** `tokens.css`, `motion.css`, `ui.css`, and `motion.js`, linked by every page. Documented in `docs/design-system.md` and rendered live at `/styleguide`.
- **Machine-readable.** `llms.txt`, `sitemap.xml`, `robots.txt`. Deployment config in `vercel.json`.

## Run it locally

Serve the folder with any static server, then open the printed URL.

```
python3 -m http.server 8000
```

## Built by Moochbot

Mooch's in-house AI agent writes the pages and ships the changes. The design system it reuses and the house rules it follows are in `CLAUDE.md`.

## Contact

- Email: hey@mooch.agency
- X: [@tahigichigi](https://x.com/tahigichigi)
- Substack: [moochagency.substack.com](https://moochagency.substack.com)
