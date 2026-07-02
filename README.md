# MarketPulse AI → UiPath (24/7, no unattended robot or VM)

Converts the local FastAPI + React app into two pieces, neither of which
depends on a laptop running `npm start` / `uvicorn`, an unattended UiPath
robot, or a VM you manage:

```
.github/workflows/marketpulse-worker.yml   GitHub Actions cron — the "always on" piece
worker/   Python — runs the real market/news/scoring/prediction/options
          logic on that schedule, writes one row to Data Fabric.
webapp/   UiPath Coded Web App (React + @uipath/uipath-typescript SDK) —
          reads that row and renders the same MarketPulse dashboard.
data-fabric/   entity + creation command for the row the worker writes to.
```

Why two pieces, not one: a **Coded Web App is a static frontend hosted on
UiPath's CDN** — it has no server process, so it can't itself run yfinance
polling every few minutes. The **worker** is the thing that's actually
"24/7," and it runs on **GitHub's own hosted runners** on a cron schedule —
not an unattended UiPath robot, not a VM you provision or patch. The web app
just displays whatever the worker last wrote to Data Fabric.

## 0. Before anything else — rotate your credentials

Your original `backend/.env` contained live keys, including a **Dhan trading
account access token**. Because that file was uploaded here, treat those
credentials as exposed:
- Rotate/regenerate the Dhan access token from your Dhan account.
- Rotate the OpenAI, NewsAPI, GNews, and Finnhub keys if you'd rather not
  reuse them.
- Never commit `.env` or paste raw keys into UiPath assets in plaintext where
  others can read them — use Orchestrator **Credential assets**, not Text
  assets, for anything secret.

This build is **signals/analysis only** — nothing here places real orders.
Keep it that way unless you deliberately design, review, and gate an
order-placement path behind its own explicit human approval step.

## 1. Create the Data Fabric entity

```bash
uip tools install @uipath/data-fabric-tool   # once
uip login status --output json               # confirm logged in

cd data-fabric
ENTITY_ID=$(uip df entities create "MarketPulseSnapshot" --file entity-body.json --output json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['Data']['Id'])")
echo "Entity ID: $ENTITY_ID"
```

That's the value both `worker/.env.production`'s `DF_ENTITY_ID` and
`webapp/.env`'s `VITE_DF_ENTITY_ID` need. Full field list and the equivalent
manual (web UI) steps are in `data-fabric/entity-schema.md`.

## 2. Deploy the worker as a GitHub Actions scheduled workflow

No unattended robot, no VM. `.github/workflows/marketpulse-worker.yml` uses
GitHub's own hosted runners as the "always on" piece.

**~1-minute cadence, on a public repo.** GitHub Actions cannot schedule cron
jobs more often than every 5 minutes — that's a hard platform limit. To get
close to a 1-minute refresh anyway, the workflow triggers every 19 minutes
and, inside that single run, **loops** `python -m app.worker` every 60
seconds for ~20 minutes, so the next scheduled tick overlaps before the
previous one finishes — no gap in coverage.

This only stays free if **the repo is public**: GitHub gives public repos
unlimited Actions minutes, but private repos get a small free quota (2,000
min/month on the Free plan) then bill per minute — and near-continuous
20-minutes-per-19-minutes looping burns that quota in hours, not days.
Making the repo public exposes the **code** (this worker's logic, the
webapp's source) to anyone — it does **not** expose secrets; `UIPATH_CLIENT_SECRET`,
API keys, etc. stay encrypted in GitHub Secrets and are never printed or
committed regardless of visibility. Before you push, double check there's
nothing else in this project (comments, sample data, filenames) you wouldn't
want public.

**1. Push this project to a public GitHub repo:**

```bash
gh repo create marketpulse-ai --public --source=. --push
```

**2. Set the secrets** — the workflow reads these as env vars at runtime;
nothing sensitive is ever committed:

```bash
# needs GitHub CLI: https://cli.github.com  (gh auth login first)
gh secret set UIPATH_BASE_URL       --body "https://cloud.uipath.com"
gh secret set UIPATH_ORG_NAME       --body "<your-org-slug>"
gh secret set UIPATH_TENANT_NAME    --body "<your-tenant>"
gh secret set UIPATH_CLIENT_ID      --body "<confidential-oauth-client-id>"
gh secret set UIPATH_CLIENT_SECRET  --body "<confidential-oauth-client-secret>"
gh secret set UIPATH_FOLDER_ID      --body "<orchestrator-folder-id>"
gh secret set DF_ENTITY_ID          --body "$ENTITY_ID"
gh secret set OPENAI_API_KEY        --body "<rotated-key>"
gh secret set DHAN_CLIENT_ID        --body "<rotated-client-id>"
gh secret set DHAN_ACCESS_TOKEN     --body "<rotated-token>"
```

`UIPATH_CLIENT_ID` / `UIPATH_CLIENT_SECRET` come from a **confidential**
External Application (client-credentials grant, not the browser-based one
the web app uses) scoped to
`DataFabric.Data.Read DataFabric.Data.Write DataFabric.Schema.Read`.
`DF_ENTITY_ID` is the `$ENTITY_ID` captured in Step 1. Only set the
`OPENAI_API_KEY` / `DHAN_*` secrets if you're keeping those integrations
enabled — and rotate them first (see Step 0).

**3. Trigger a first run to confirm it works:**

```bash
gh workflow run marketpulse-worker.yml   # manual run to test immediately
gh run watch                              # follow it live
```

After that, GitHub's scheduler fires a new 20-minute looping run every 19
minutes on its own — nothing to keep running locally, and within each run
the dashboard refreshes about once a minute. First cycle creates the Data
Fabric row; every cycle after that updates it (`df_client.py` looks up the
existing row id and upserts). Adjust the loop's `sleep 60` / cron expression
in the workflow file if you want a different cadence — check GitHub's [cron
syntax docs](https://docs.github.com/actions/using-workflows/events-that-trigger-workflows#schedule) —
note that scheduled workflows are paused automatically if the repo has no
activity for 60 days, so you'll need to push a commit or manually re-enable
it if that happens.

**Local smoke test before pushing:**

```bash
cd worker
cp .env.example .env.production   # fill in the same values as the secrets above
python -m app.worker
```

`worker.py` loads `.env.production` automatically for local runs; in GitHub
Actions the secrets above are injected directly as env vars, so no file is
needed there. `.gitignore` already excludes `.env` / `.env.production` so
your local copy never gets pushed.

## 3. Scaffold and deploy the Coded Web App

The `webapp/` folder already has the source files (`App.tsx`, `Dashboard.tsx`,
`dataClient.ts`, `useAuth.tsx`) — you still need to run the actual scaffold +
publish commands from your machine against your real UiPath tenant, since
that requires your login and org/tenant/Client ID (values I don't have here):

```bash
npm install -g @uipath/cli
uip tools install @uipath/codedapp-tool
uip tools install @uipath/orchestrator-tool
uip login                      # opens a browser
```

Create an OAuth **External Application** (interactive/browser type) with
redirect URI `http://localhost:5173` and scope
`DataFabric.Data.Read DataFabric.Schema.Read`, then fill in `webapp/.env`
(copy from `.env.example`) and `webapp/uipath.json` with that Client ID, your
org, tenant, base URL, and the `DF_ENTITY_ID` from step 1.

```bash
cd webapp
npm install
npm install @uipath/uipath-typescript --@uipath:registry=https://registry.npmjs.org
npm run build                          # verify dist/ exists
uip codedapp pack dist -n marketpulse --version 1.0.0
uip codedapp publish                   # writes .uipath/app.config.json
uip or folders list --output json      # find your folder's Key
uip codedapp deploy -n marketpulse --folder-key <GUID>
```

The final command prints the live app URL — that's the always-on dashboard,
refreshing from Data Fabric every 30s, independent of anyone's laptop.

## What changed from the original app

- `backend/app/main.py`'s `/dashboard` endpoint logic → `worker/app/worker.py`
  (`build_snapshot()`), same service modules (`market.py`, `news.py`,
  `scoring.py`, `prediction.py`, `decision.py`, `alerts.py`, `options.py`,
  `trade.py`, `sector.py`, `insight.py`, `dhan_options.py`) reused as-is.
- The `/ws` websocket heartbeat and Redis cache (`core/cache.py`) were unused
  by any service and dropped — Data Fabric is now the shared state instead.
- `frontend/src/App.js` (axios → `localhost:8000`) → `webapp/src/Dashboard.tsx`
  (UiPath SDK → Data Fabric), same layout and colors.
- Trade engine output is now explicitly labeled "informational only" in the UI.
- Scheduling runs on GitHub Actions cron rather than an unattended UiPath
  robot or a self-managed VM/server, per your preference — see Step 2.
