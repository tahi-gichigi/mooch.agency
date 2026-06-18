# Mooch design system

Small and flat by design. No framework, no build step. Four shared files, linked
by every page, hold everything that used to be copy-pasted into each `.html` and
drift. Page-specific layout stays inline in each page's `<style>`.

Rendered reference: `styleguide.html` (`/styleguide`, noindex, not in the sitemap)
draws every token, button and motion from the same shared files, so it shows the
real shipped values. This doc is its prose companion.

## The shared files

- **`tokens.css`** — the single `:root`. Colour, type, spacing, radius, and all
  motion timing (easings, durations, the stagger scale). Change a value here and
  it moves site-wide. A page may still override any token in its own `:root`
  (the dark footer lightens `--muted` locally, for example).
- **`motion.css`** — entrance motion: `.reveal` (+ `.d1`–`.d4`), the per-word
  `.reveal-words .word`, and scroll `.rise`. Includes the reduced-motion guards.
  Palette-agnostic; references the tokens.
- **`ui.css`** — canonical `.pill` and `.ghost` buttons, anchored to the homepage
  hero values. Focus rings and the `aria-disabled` state live here too.
- **`motion.js`** — declarative entrance logic, read by `index.html`. Reads its
  timing from `tokens.css`. Two hooks:
  - `data-stagger` on an element splits its text into per-word reveals.
  - `data-reveal="child: <selector>; cap: <n>"` on a container scroll-reveals its
    children, staggered on `--stagger-beat`, capped at `<n>`.

Entrance and stagger timing sits 25% slower than the original feel. Deliver-mode
timing (`--t-deliver`, hover and press) stays snappy and is never slowed.

## Linking, by page type

| Page | tokens.css | motion.css | ui.css | motion.js |
|------|:--:|:--:|:--:|:--:|
| Homepage (`index.html`) | yes | yes | yes | yes |
| `ready.html` | yes | yes | yes | no (own quiz JS) |
| Case studies + template | yes | yes | no | no (CSS-only `.reveal`) |
| `404.html` | yes | no | no | no |

Case studies need no JS: their entrances are pure-CSS `.reveal` classes. `404` has
no motion at all, so it links only `tokens.css`. Only the homepage uses the
scroll-reveal and word-stagger that `motion.js` drives.

## Adding a new page

1. Copy `case-study-template.html` (or `index.html` for a marketing page).
2. Keep the four `<link>` lines in the head: `tokens.css`, then `motion.css`,
   then `ui.css`. Add `motion.js` before `</body>` only if the page uses
   `data-reveal` / `data-stagger`.
3. Put only page-specific layout in the inline `<style>`. Never redefine a token
   that `tokens.css` already provides.
4. Use `.pill` / `.ghost` for buttons. Don't restyle them per page.
5. Add the page to `sitemap.xml` and `llms.txt` if it's public.
