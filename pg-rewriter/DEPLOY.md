# Deploy: Write Like Paul Graham

The tool lives in this repo: `paulgraham.html` (the page), `api/rewrite.js` (the
streaming function), `api/pg-system.md` (the system prompt, generated from
`pg-rewriter/voice/`), and `vercel.json` (the host rewrite).

## How it deploys

The repo deploys as the `mooch.agency` Vercel project from `master`. Merging to
`master` ships `/api/rewrite` and `/paulgraham`. The host rewrite in `vercel.json`
is conditional on `paulgraham.mooch.agency`, so `mooch.agency` itself is untouched.

To put it on its own subdomain, add `paulgraham.mooch.agency` to the project and
point a DNS record at Vercel (`CNAME paulgraham -> cname.vercel-dns.com`, DNS-only).
Vercel issues the certificate.

## Environment variables

Set these on the Vercel project (Production):

- `OPENAI_API_KEY`: required. The rewriter's OpenAI key.
- `PROVIDER`: `openai` (default) or `claude`.
- `ANTHROPIC_API_KEY`: only if `PROVIDER=claude`.
- `OPENAI_MODEL` / `CLAUDE_MODEL`: optional overrides (defaults `gpt-5.5` and `claude-sonnet-4-6`).
- `REWRITER_DISABLED`: set to `1` to pause the tool without redeploying.

## Model

gpt-5.5 is the default, chosen on a bake-off against gpt-5-mini, Sonnet 4.6, and
Opus 4.8: it leads on PG-fit and reads cleanest (see `voice/test/RESULTS.md`).
Claude is a one-variable fallback (`PROVIDER=claude`).

## Verify

- `curl -N -X POST https://paulgraham.mooch.agency/api/rewrite -H 'content-type: application/json' -d '{"text":"It could be argued that..."}'` streams `data:` tokens.
- Load the page, paste, hit Rewrite, watch the before/after Voice Score, copy.

## Cost guards

A server word cap, a conservative `max_tokens`, a best-effort per-instance rate
limit, an origin check, and the `REWRITER_DISABLED` kill switch. Set a monthly
spend ceiling in the provider console too.

## Parked for v2

A live "N paragraphs rewritten" counter and a durable rate limit, both of which
need a store (Cloudflare KV or similar).
