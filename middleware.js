// Dream Menu sign-in for the partner area and the full report pages (Vercel Routing Middleware).
// The password is NOT stored in this file. Set it in Vercel: Project > Settings > Environment Variables,
// name DM_PASSWORD, environment Production. If DM_PASSWORD is missing, every locked page stays locked.
// Individual partner passwords: slow one-way hashes in the KEYS block below, managed with
// tools/partner_passwords.py (add / revoke / list). They work alongside DM_PASSWORD and never replace it.
// This only works when the site is deployed with the Vercel CLI (a build step); a drag-and-drop upload
// publishes files as-is and skips middleware.
export const config = { matcher: [
  '/briefing', '/briefing/:path*', '/briefing.html', '/onepager', '/onepager.html', '/review', '/review.html',
  '/geocoder', '/geocoder.html', '/partner-data.js',
  '/report/:path+', '/operators', '/operators.html', '/tested-ideas', '/tested-ideas.html',
  '/insights', '/insights.html', '/case-studies', '/case-studies.html', '/case-studies/:path*', '/partner', '/partner.html', '/partner/:path*',
  '/login', '/logout'] };

const COOKIE = 'dm_partner';
const PUBLIC = new Set(['/case-studies/guests-and-critics', '/case-studies/guests-and-critics.html']);
async function token(pw) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(String(pw).trim().toLowerCase() + '|dream-menu-v2'));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
}
async function expected() {
  const pw = (typeof process !== 'undefined' && process.env && process.env.DM_PASSWORD) || '';
  return pw ? token(pw) : null;            // no main password configured: only individual keys work
}
const KEYS = new Map([
// partner-keys:start
  ['f1d594f74bf0a60edf55906b3ecc05a0f7a428d6932a4229976cb0d5bbe42861', 'partner-02'], // Partner 02 (added 2026-11-12)
  ['0f4c7d20dcf1787f1dff494291d40ee4346303b7277790ad9f1b530e040b0b18', 'partner-03'], // Partner 03 (added 2026-11-12)
  ['5678754aa3472a39799b286cd68d56db1d50f5f836027043fee5f20242c8f9dd', 'partner-04'], // Partner 04 (added 2026-11-12)
  ['3079943a5bab563556fb5dff67827f97220eb22932664ad695c36b757dc434ec', 'partner-05'], // Partner 05 (added 2026-11-12)
  ['ce60c6d8c0e244b894609883307f258de0efea7a48056439f99a4ef9985c52db', 'partner-06'], // Partner 06 (added 2026-11-12)
  ['1239f12d7cf130d2a509a2bbeeda045bc01b56b2d6afb5f13a150d5edf96acf3', 'partner-07'], // Partner 07 (added 2026-11-12)
  ['d707c29b143b359094153343c5adebda7425956f576a42a030f4e7ca55f72881', 'partner-08'], // Partner 08 (added 2026-11-12)
  ['9c6b2ddfd9994d935cdd9dc155ae7a748126619f10c78c43b4272f81dc35dab9', 'partner-09'], // Partner 09 (added 2026-11-12)
  ['b90e62d9216c4eea5acd29da0fb3d643ac9bee2ac7b3ca2520b21e9d500b17ac', 'partner-10'], // Partner 10 (added 2026-11-12)
  ['f84fd8474f8877943d4d6fef5c2625c7fd5656fd24bfb2b492f06a5e1cca1feb', 'partner-11'], // Partner 11 (added 2026-11-12)
// partner-keys:end
]);
async function keyToken(pw) {              // PBKDF2, so the stored hashes cannot be guessed back into passwords
  const enc = new TextEncoder();
  const k = await crypto.subtle.importKey('raw', enc.encode(String(pw).trim().toLowerCase()), 'PBKDF2', false, ['deriveBits']);
  const buf = await crypto.subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt: enc.encode('dream-menu-partner-key-v1'), iterations: 100000 }, k, 256);
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
}
const next = () => new Response(null, { headers: { 'x-middleware-next': '1' } });
const go = (url, cookie, who) => {
  const h = new Headers({ Location: url, 'Cache-Control': 'no-store' });
  if (cookie) h.append('Set-Cookie', cookie);
  // dm_who is a plain label (never the password) so the site can count visits per partner; see nav.js
  if (who !== undefined) h.append('Set-Cookie', `dm_who=${who}; Path=/; Max-Age=${who ? 2592000 : 0}; Secure; SameSite=Lax`);
  return new Response(null, { status: 303, headers: h });
};
const safe = p => (p && p.startsWith('/') && !p.startsWith('//')) ? p : '/analysis';

export default async function middleware(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  const want = await expected();
  if (path === '/logout') return go('/', `${COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax`, '');
  if (path === '/login') {
    if (request.method === 'POST') {
      const form = await request.formData();
      const to = safe(form.get('next'));
      const pw = form.get('password') || '';
      if (want && (await token(pw)) === want)
        return go(to, `${COOKIE}=${want}; Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Lax`, 'main');
      if (KEYS.size && String(pw).trim().length >= 12) {
        const kt = await keyToken(pw);
        if (KEYS.has(kt)) return go(to, `${COOKIE}=${kt}; Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Lax`, KEYS.get(kt));
      }
      return go('/login?e=1&next=' + encodeURIComponent(to));
    }
    return next();
  }
  if (PUBLIC.has(path)) return next();       // free sample report, open to everyone
  const have = (request.headers.get('cookie') || '').split(/;\s*/).find(c => c.startsWith(COOKIE + '='));
  const got = have ? have.slice(COOKIE.length + 1) : '';
  if (got && ((want && got === want) || KEYS.has(got))) return next();   // a revoked key stops working at once
  if (path.endsWith('.js') || path.endsWith('.csv')) return new Response('Sign in required', { status: 401, headers: { 'Cache-Control': 'no-store' } });
  return go('/login?next=' + encodeURIComponent(path.replace(/\.html$/, '')));
}
