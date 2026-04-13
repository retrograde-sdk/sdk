const GAME_CDN = 'https://html5.gamemonetize.co';
const IMAGE_CDN = 'https://img.gamemonetize.com';
const API_CDN = 'https://api.gamemonetize.com';
const UNCACHED_CDN = 'https://uncached.gamemonetize.co';
const CDN_CDN = 'https://cdn.gamemonetize.com';
const SELF_ORIGIN = '';

const URL_REWRITES = [
  [/https?:\/\/api\.gamemonetize\.com\//g, '/api/'],
  [/https?:\/\/uncached\.gamemonetize\.co\//g, '/uncached/'],
  [/https?:\/\/html5\.gamemonetize\.co\//g, '/game/'],
  [/https?:\/\/html5\.gamemonetize\.com\//g, '/game/'],
  [/https?:\/\/img\.gamemonetize\.com\//g, '/img/'],
  [/https?:\/\/cdn\.gamemonetize\.com\//g, '/cdn/'],
];

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;
    const selfOrigin = url.origin;

    if (path === '/' || path === '/health') {
      return new Response('RetroArcade Proxy - Active', {
        status: 200,
        headers: { 'Content-Type': 'text/plain' }
      });
    }

    if (path.startsWith('/game/')) {
      const targetPath = path.slice(6);
      const targetUrl = GAME_CDN + '/' + targetPath + url.search;
      return proxyRequest(request, targetUrl, selfOrigin, true);
    }

    if (path.startsWith('/img/')) {
      const targetPath = path.slice(5);
      const targetUrl = IMAGE_CDN + '/' + targetPath;
      return proxyRequest(request, targetUrl, selfOrigin, false);
    }

    if (path.startsWith('/api/')) {
      const targetPath = path.slice(5);
      const targetUrl = API_CDN + '/' + targetPath + url.search;
      return proxyRequest(request, targetUrl, selfOrigin, false);
    }

    if (path.startsWith('/uncached/')) {
      const targetPath = path.slice(9);
      const targetUrl = UNCACHED_CDN + '/' + targetPath + url.search;
      return proxyRequest(request, targetUrl, selfOrigin, false);
    }

    if (path.startsWith('/cdn/')) {
      const targetPath = path.slice(5);
      const targetUrl = CDN_CDN + '/' + targetPath + url.search;
      return proxyRequest(request, targetUrl, selfOrigin, true);
    }

    return new Response('Not Found', { status: 404 });
  }
};

async function proxyRequest(request, targetUrl, selfOrigin, rewriteHtml) {
  try {
    const headers = new Headers(request.headers);
    headers.delete('host');
    headers.delete('cf-connecting-ip');
    headers.delete('cf-ray');
    headers.delete('cf-visitor');
    headers.delete('cf-worker');
    headers.set('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
    headers.set('Referer', GAME_CDN + '/');

    const response = await fetch(targetUrl, {
      method: request.method,
      headers: headers,
      body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
      redirect: 'follow',
    });

    const newHeaders = new Headers(response.headers);
    newHeaders.set('Access-Control-Allow-Origin', '*');
    newHeaders.set('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
    newHeaders.set('Access-Control-Allow-Headers', '*');
    newHeaders.set('Cache-Control', 'public, max-age=86400');
    newHeaders.delete('X-Frame-Options');
    newHeaders.delete('Content-Security-Policy');
    newHeaders.delete('Content-Security-Policy-Report-Only');

    if (rewriteHtml) {
      const contentType = newHeaders.get('Content-Type') || '';
      if (contentType.includes('text/html') || contentType.includes('application/xhtml')) {
        let body = await response.text();
        for (const [pattern, replacement] of URL_REWRITES) {
          body = body.replace(pattern, selfOrigin + replacement);
        }
        newHeaders.set('Content-Length', new TextEncoder().encode(body).length.toString());
        return new Response(body, {
          status: response.status,
          statusText: response.statusText,
          headers: newHeaders,
        });
      }
    }

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: newHeaders,
    });
  } catch (err) {
    return new Response('Proxy Error: ' + err.message, { status: 502 });
  }
}
