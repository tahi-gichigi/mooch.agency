import { rewrite, next } from '@vercel/edge';

// The subdomain paulgraham.mooch.agency serves the Paul Graham tool at its
// root. The page itself lives at /paulgraham (paulgraham.html), so rewrite the
// subdomain root to it. A rewrite (not a redirect) keeps the URL clean, and
// middleware runs before the filesystem, so it wins over index.html at "/".
// Only "/" is matched, so assets, /api and every other path are untouched.
export const config = { matcher: '/' };

export default function middleware(request) {
  const host = request.headers.get('host') || '';
  if (host === 'paulgraham.mooch.agency') {
    return rewrite(new URL('/paulgraham', request.url));
  }
  return next();
}
