# Cloudflare Worker proxy — setup

This gives the web app genuinely fresh data (seconds, not minutes) by
proxying GitHub's live Contents API instead of a cached static-file CDN.

## 1. Create a GitHub personal access token

- GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
- Generate new token, scope: `public_repo` (repo is public, this is enough)
- Copy the token — you won't see it again

## 2. Create the Worker (Cloudflare dashboard, no CLI needed)

- Sign up free at https://dash.cloudflare.com (no credit card required for the free tier)
- Workers & Pages → Create → Create Worker
- Give it a name, e.g. `marketpulse-proxy` — note the resulting URL, something like:
  `https://marketpulse-proxy.<your-subdomain>.workers.dev`
- Click "Edit code" and paste in the full contents of `worker.js` from this folder
- Deploy

## 3. Add the GitHub token as a secret

- In the Worker's dashboard: Settings → Variables and Secrets → Add
- Name: `GITHUB_TOKEN`, Type: Secret, Value: the token from step 1
- Save (this redeploys the Worker automatically)

## 4. Test it directly

```bash
curl -s "https://marketpulse-proxy.<your-subdomain>.workers.dev" | python3 -m json.tool
```

Should return the same JSON as `data/snapshot.json` in the repo, with no
CORS errors when called from a browser. Run it twice in a row right after
the worker writes a new cycle — it should reflect changes within seconds,
not minutes.

## 5. Point the web app at it

Update `webapp/src/dataClient.ts`'s `SNAPSHOT_URL` to your Worker's URL
instead of the jsDelivr one, then rebuild and redeploy the Coded Web App as
usual.
