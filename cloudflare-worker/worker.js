// Cloudflare Worker: proxies GitHub's live Contents API (not the cached
// raw-file CDN) so the browser gets genuinely fresh data with proper CORS
// headers. Deploy via the Cloudflare dashboard (Workers & Pages -> Create
// Worker -> paste this in) or via `wrangler deploy` if you use the CLI.
//
// Requires one secret, set in the Worker's settings (not in this file):
//   GITHUB_TOKEN  a GitHub personal access token with read access to the
//                 repo's contents (classic PAT with "public_repo" scope
//                 is enough since the repo is public)

const REPO = 'ksinha01/marketpulse-ai';
const FILE_PATH = 'data/snapshot.json';
const BRANCH = 'main';

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    try {
      const url = `https://api.github.com/repos/${REPO}/contents/${FILE_PATH}?ref=${BRANCH}`;
      const resp = await fetch(url, {
        headers: {
          Authorization: `token ${env.GITHUB_TOKEN}`,
          Accept: 'application/vnd.github.raw',
          'User-Agent': 'marketpulse-worker-proxy',
        },
        // Cloudflare's own edge cache — explicitly disabled, this is the
        // whole point of this proxy existing.
        cf: { cacheTtl: 0, cacheEverything: false },
      });

      if (!resp.ok) {
        const errText = await resp.text();
        return new Response(
          JSON.stringify({ error: 'github_fetch_failed', status: resp.status, detail: errText }),
          { status: 502, headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' } }
        );
      }

      const body = await resp.text(); // already raw JSON from the Accept header above
      return new Response(body, {
        status: 200,
        headers: {
          ...CORS_HEADERS,
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store',
        },
      });
    } catch (err) {
      return new Response(
        JSON.stringify({ error: 'proxy_exception', detail: String(err) }),
        { status: 500, headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' } }
      );
    }
  },
};
