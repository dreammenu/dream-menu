// Dream Menu sign-in for the partner area and the full report pages (Vercel Routing Middleware).
// The password is NOT stored in this file. Set it in Vercel: Project > Settings > Environment Variables,
// name DM_PASSWORD, environment Production. If DM_PASSWORD is missing, every locked page stays locked.
// This only works when the site is deployed with the Vercel CLI (a build step); a drag-and-drop upload
// publishes files as-is and skips middleware.
export const config = { matcher: [
  '/briefing', '/briefing/:path*', '/briefing.html', '/onepager', '/onepager.html', '/review', '/review.html',
  '/geocoder', '/geocoder.html', '/partner-data.js',
  '/report/:path+', '/operators', '/operators.html', '/tested-ideas', '/tested-ideas.html',
  '/insights', '/insights.html', '/case-studies', '/case-studies.html', '/case-studies/:path*', '/intelligence', '/intelligence.html', '/partner', '/partner.html', '/partner/:path*',
  '/login', '/logout'] };

const COOKIE = 'dm_partner';
const PUBLIC = new Set(['/case-studies/guests-and-critics', '/case-studies/guests-and-critics.html']);
async function token(pw) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(String(pw).trim().toLowerCase() + '|dream-menu-v2'));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
}
async function expected() {
  const pw = (typeof process !== 'undefined' && process.env && process.env.DM_PASSWORD) || '';
  return pw ? token(pw) : null;            // no password configured: fail closed
}
const next = () => new Response(null, { headers: { 'x-middleware-next': '1' } });
const go = (url, cookie) => {
  const h = new Headers({ Location: url, 'Cache-Control': 'no-store' });
  if (cookie) h.append('Set-Cookie', cookie);
  return new Response(null, { status: 303, headers: h });
};
const safe = p => (p && p.startsWith('/') && !p.startsWith('//')) ? p : '/partner';

export default async function middleware(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  const want = await expected();
  if (path === '/logout') return go('/', `${COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax`);
  if (path === '/login') {
    if (request.method === 'POST') {
      const form = await request.formData();
      const to = safe(form.get('next'));
      if (want && (await token(form.get('password') || '')) === want)
        return go(to, `${COOKIE}=${want}; Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Lax`);
      return go('/login?e=1&next=' + encodeURIComponent(to));
    }
    return next();
  }
  if (PUBLIC.has(path)) return next();       // free sample report, open to everyone
  const have = (request.headers.get('cookie') || '').split(/;\s*/).find(c => c.startsWith(COOKIE + '='));
  if (want && have && have.slice(COOKIE.length + 1) === want) return next();
  if (path.endsWith('.js') || path.endsWith('.csv')) return new Response('Sign in required', { status: 401, headers: { 'Cache-Control': 'no-store' } });
  return go('/login?next=' + encodeURIComponent(path.replace(/\.html$/, '')));
}
