# Best Practices Report: mooch.agency

**Date:** 01 Jul 2026
**Mode:** apply (safe fixes applied, remainder flagged)
**Pages audited:** 18 HTML files + sitemap.xml + robots.txt + llms.txt

## Summary

| Discipline | Status | Findings |
| --- | --- | --- |
| SEO/meta | PASS | 6 issues (3 high, 2 medium, 1 low). 4 auto-fixed. |
| Accessibility | PASS (94) | 4 issues (1 high, 2 medium, 1 low). 0 auto-fixed (all need design decisions). |
| Performance | PASS (87) | 3 issues (1 medium, 2 low). Lighthouse mobile: 87/100. Close to 90 budget. |
| Design-system | FAIL | 7 issues (2 high, 3 medium, 2 low). 0 auto-fixed (need design review). |
| Security | FAIL | 2 issues (1 high, 1 low). 1 auto-fixed (headers added to vercel.json). |
| Privacy | PASS | 1 issue (1 medium). No cookies, so no consent banner needed. |
| Content hygiene | PASS | 2 issues (1 medium, 1 low). 1 auto-fixed (noindex on portfolio pages). |
| Mobile/responsive | PASS | 1 issue (1 low). All pages have viewport meta. |
| Trust | PASS | 1 issue (1 low). Footer complete with company, email, social. |
| Analytics | PASS | 1 issue (1 medium). Speed Insights missing on paulgraham.html (auto-fixed). |

**Total:** 28 findings (0 critical, 4 high, 9 medium, 9 low, 6 info)
**Auto-fixed this run:** 6 items
**Remaining manual:** 16 actionable items (excluding 6 info-level "no action needed")

## Applied fixes

| File | Change |
| --- | --- |
| `portfolio-all.html` | Added `<meta name="robots" content="noindex, nofollow">` |
| `portfolio-explorations.html` | Added `<meta name="robots" content="noindex, nofollow">` |
| `portfolio-explorations-2.html` | Added `<meta name="robots" content="noindex, nofollow">` |
| `404.html` | Added `<meta name="robots" content="noindex">` |
| `vercel.json` | Added security headers: X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, Content-Security-Policy |
| `paulgraham.html` | Added Speed Insights script tag |
| `tokens.css` | Added `--error: #b00020` token |

## High

### SEO/meta: Draft pages missing noindex
- **Files:** `portfolio-all.html`, `portfolio-explorations.html`, `portfolio-explorations-2.html`
- **Fix:** Added `<meta name="robots" content="noindex, nofollow">` to all 3.
- **Status:** APPLIED

### SEO/meta: Portfolio pages missing all core meta tags
- **Files:** `portfolio-all.html`, `portfolio-explorations.html`, `portfolio-explorations-2.html`
- **Fix:** Add meta description, canonical, OG tags, Twitter card, and favicons. Even with noindex, shared links render with no context.
- **Status:** MANUAL (needs content decisions for descriptions)

### Accessibility: --muted contrast at small sizes
- **File:** `tokens.css` (line 10)
- **Detail:** `--muted: #6e6e73` is ~4.9:1 on white, borderline at 10-11px sizes used in `.colophon-sep`, `.topbar .you`, `case-meta dt`, `.colophon-version`.
- **Fix:** Darken `--muted` (e.g. `#5a5a5f` for ~7:1) or introduce `--muted-small` for footer/meta text.
- **Status:** MANUAL (design decision)

### Design-system: Prompt pages bypass shared CSS entirely
- **Files:** `prompts/deslop.html`, `prompts/soundlikeme.html`, `prompt-template.html`
- **Detail:** These pages don't link `tokens.css`, `ui.css`, or `motion.css`. They hand-copy the entire `:root` block inline and reimplement `.reveal` with different timing.
- **Fix:** Add `<link>` tags for shared CSS per CLAUDE.md order, remove duplicated inline `:root` and `.reveal`.
- **Status:** MANUAL (needs testing to confirm shared CSS doesn't break these layouts)

### Security: No security headers configured
- **File:** `vercel.json`
- **Fix:** Added headers block with CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy.
- **Status:** APPLIED

## Medium

### SEO/meta: 404 page missing noindex and meta tags
- **File:** `404.html`
- **Fix:** noindex added. OG/Twitter tags still missing (low priority for a 404).
- **Status:** PARTIAL (noindex applied, meta tags remain manual)

### SEO/meta: sitemap.xml completeness
- **File:** `sitemap.xml`
- **Detail:** `/ready` is listed in the sitemap (confirmed). `/prompts/soundlikeme` and `/prompts/deslop` are listed but have no matching HTML files in the repo (may be served via redirect or another mechanism).
- **Fix:** Verify the prompt routes resolve. If they 404, remove from sitemap.
- **Status:** MANUAL (needs verification)

### Accessibility: Missing landmark elements
- **Files:** `portfolio-explorations.html`, `portfolio-explorations-2.html`, `404.html`, `paulgraham.html`
- **Fix:** Wrap content in `<main>`, add `<header>`/`<footer>` matching other pages.
- **Status:** MANUAL

### Accessibility: paulgraham.html has no heading elements
- **File:** `paulgraham.html`
- **Fix:** Verify content structure, add h1-h3 hierarchy.
- **Status:** MANUAL

### Design-system: Dark footer overrides duplicated across 8+ files
- **Files:** All case study pages + prompt pages
- **Detail:** `--muted: #8e8e93` and `#2a2a2c` hairline overrides copy-pasted everywhere.
- **Fix:** Promote to a shared `.colophon` dark-footer utility in `ui.css` or `tokens.css`.
- **Status:** MANUAL

### Design-system: Portfolio pages redefine full `:root` locally
- **Files:** `portfolio-all.html`, `portfolio-explorations.html`, `portfolio-explorations-2.html`
- **Fix:** Link `tokens.css` directly, add any new tint variants to `tokens.css`.
- **Status:** MANUAL

### Design-system: No error/danger colour token
- **File:** `tokens.css`
- **Fix:** Added `--error: #b00020` to the palette.
- **Status:** APPLIED (token added; instances in pages should use `var(--error)` going forward)

### Privacy: No privacy policy page
- **File:** n/a
- **Detail:** No privacy policy exists anywhere. No cookies are set, so no legal requirement yet. But good practice for any site with analytics.
- **Fix:** Write and publish a privacy policy, link from footer.
- **Status:** MANUAL

### Analytics: paulgraham.html missing Speed Insights
- **File:** `paulgraham.html`
- **Fix:** Added `<script defer src="/_vercel/speed-insights/script.js"></script>`.
- **Status:** APPLIED

## Low

### SEO/meta: Page titles shorter than ideal
- **Detail:** All live pages have titles in the 27-44 char range; the ideal is 50-60. More descriptive titles would use more SERP space.
- **Status:** MANUAL

### SEO/meta: Meta descriptions shorter than ideal
- **Detail:** Several case studies have descriptions under 120 chars. Expanding to 120-160 chars would capture more SERP snippet space.
- **Status:** MANUAL

### Accessibility: --hairline contrast
- **File:** `ui.css`
- **Detail:** `--hairline: #d2d2d7` is only 1.5:1 against white. Fine for decorative dividers, but insufficient for interactive element borders.
- **Fix:** Audit usages; swap to a darker token where it borders a focusable element.
- **Status:** MANUAL

### Design-system: .copy-btn meets rule-of-three
- **Files:** Prompt pages
- **Detail:** `.copy-btn` is used in 3 files but not promoted to `ui.css`.
- **Fix:** Promote to `ui.css`, add to `styleguide.html`.
- **Status:** MANUAL

### Design-system: paulgraham.html .settle animation
- **File:** `paulgraham.html`
- **Detail:** `.settle` is a bespoke reveal-style keyframe duplicating `motion.css .reveal`.
- **Fix:** Evaluate whether it can be replaced by `.reveal` or documented as an intentional variant.
- **Status:** MANUAL

### Security: No lockfile for npm audit
- **File:** `package.json`
- **Detail:** No `package-lock.json`, so `npm audit` can't run. Low risk given only 1 dependency (`@vercel/edge`).
- **Fix:** Run `pnpm install --lockfile-only` to generate a lockfile.
- **Status:** MANUAL

### Mobile: No responsive images
- **Detail:** No `srcset` or `<picture>` elements. All images are flat `<img src>`.
- **Fix:** Add `srcset`/`sizes` for large hero images to serve smaller variants on mobile.
- **Status:** MANUAL

### Trust: No phone contact
- **Detail:** No `tel:` link anywhere. Likely intentional for an email-first agency.
- **Status:** MANUAL (confirm with Tahi)

### Content hygiene: Template placeholder text
- **Files:** `case-study-template.html`, `prompt-template.html`
- **Detail:** Contain `[Project name]`/`[Prompt name]` placeholders. Both are correctly noindexed templates.
- **Status:** No action needed.

## Info (no action needed)

- Broken links: 0/27 (linkinator clean run)
- robots.txt: valid
- llms.txt: present
- Copyright: 2026, current
- Cookies: none set, no consent banner needed
- Third-party scripts: Google Fonts only (low risk)
- Focus-visible, reduced-motion, heading order, alt text: all pass
- Viewport meta: present on all 18 pages
- Footer: complete (company name, email, social)
- Vercel Analytics: present on all live pages
- No PII in analytics event payloads
- No leaked secrets in source

## Performance (Lighthouse mobile)

| Metric | Score |
| --- | --- |
| Performance | 87/100 |
| Accessibility | 94/100 |
| Best Practices | 100/100 |
| SEO | 100/100 |

Key performance items below budget:
- First Contentful Paint: needs improvement (score 0.63)
- Cumulative Layout Shift: needs improvement (score 0.78)
- Render-blocking resources present

## Tools used

- `npx lighthouse` (v13.4.0): performance, accessibility, SEO, best-practices
- `npx linkinator` (v7.6.1): broken link detection
- File-level grep and analysis: design-system conformance, security secrets, content hygiene
