# MarketPulse AI → UiPath (24/7, no unattended robot or VM)

Converts the local FastAPI + React app into two pieces, neither of which
depends on a laptop running `npm start` / `uvicorn`, an unattended UiPath
robot, or a VM you manage:

```
.github/workflows/marketpulse-worker.yml   GitHub Actions cron — the "always on" piece
worker/   Python — runs the real market/news/scoring/prediction/options
          logic on that schedule, overwrites one Orchestrator Text asset.
webapp/   UiPath Coded Web App (React + @uipath/uipath-typescript SDK) —
          reads that asset and renders the same MarketPulse dashboard.
```

Why two pieces, not one: a **Coded Web App is a static frontend hosted on
UiPath's CDN** — it has no server process, so it can't itself run yfinance
polling every few minutes. The **worker** is the thing that's actually
"24/7," and it runs on **GitHub's own hosted runners** on a cron schedule —
not an unattended UiPath robot, not a VM you provision or patch. The web app
just displays whatever the worker last wrote.

**Why an Orchestrator Asset and not Data Fabric:** Data Fabric was the
original design, but its record-level API (`records list/insert/update`)
rejected the worker's confidential-app (client-credentials) identity outright
— `"You don't have permission to access the entity, field or record or you
are using an unsupported robot type"` — in every configuration tested:
correct DataFabric scopes, correct entity permissions (RBAC confirmed off),
tenant IP restriction confirmed disabled, and even a restored real
interactive-user session hit the identical error. Schema-level Data Fabric
calls (`entities get/list`) worked fine for the same identity; only
record-level calls failed. The same confidential-app identity was directly
tested and confirmed working against Orchestrator Assets, so the whole
snapshot is stored there instead — one Text asset (`MarketPulseSnapshot`)
that the worker overwrites every cycle.

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

## 1. Create the Orchestrator asset

```bash
uip tools install @uipath/orchestrator-tool   # once
uip login status --output json                # confirm logged in

uip or assets create "MarketPulseSnapshot" "{}" --folder-path "Shared" --type Text --output json

# Note the Key (a UUID) from that response's Data field, or look it up:
ASSET_KEY=$(uip or assets list --folder-path "Shared" --name "MarketPulseSnapshot" --output json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['Data'][0]['Key'])")
echo "Asset key: $ASSET_KEY"
```

Use whatever folder path fits your tenant — `Shared` is the top-level
default folder in most tenants. `$ASSET_KEY` is the value both
`worker/.env.production`'s `ASSET_KEY` and the `ASSET_KEY` GitHub secret
need — note it's the asset's **key** (a UUID), not its name; `update` and
`get-asset-value` both require the key.

## 2. Deploy the worker as a GitHub Actions scheduled workflow

No unattended robot, no VM. `.github/workflows/marketpulse-worker.yml` uses
GitHub's own hosted runners as the "always on" piece, authenticating as your
confidential/client-credentials External Application — confirmed working
against Orchestrator Assets (see the architecture note above for why this
identity was tested against both Data Fabric and Assets before landing here).

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
Making the repo public exposes the **code** to anyone — it does **not**
expose secrets; they stay encrypted in GitHub Secrets and are never printed
or committed regardless of visibility. Before you push, double check there's
nothing else in this project (comments, sample data, filenames) you wouldn't
want public.

**1. Push this project to a public GitHub repo:**

```bash
gh repo create marketpulse-ai --public --source=. --push
```

**2. Create a confidential External Application** in UiPath Admin
(client-credentials grant, not the browser-based one the web app uses),
scoped to `OR.Assets`. Set its ID/secret/tenant as secrets:

```bash
gh secret set UIPATH_CLIENT_ID
gh secret set UIPATH_CLIENT_SECRET
gh secret set UIPATH_TENANT_NAME
gh secret set ASSET_KEY              # the UUID from Step 1
gh secret set ASSET_FOLDER_PATH      # e.g. "Shared"
gh secret set OPENAI_API_KEY         # only if keeping this integration — rotate first (Step 0)
gh secret set DHAN_CLIENT_ID         # only if keeping this integration — rotate first (Step 0)
gh secret set DHAN_ACCESS_TOKEN      # only if keeping this integration — rotate first (Step 0)
```

Running `gh secret set NAME` with no `--body` prompts you to paste the value
interactively — this avoids both shell-quoting issues with special
characters like `!` and leaving secret values in your terminal history.

**3. Trigger a first run to confirm it works:**

```bash
gh workflow run marketpulse-worker.yml   # manual run to test immediately
gh run watch                              # follow it live
```

After that, GitHub's scheduler fires a new 20-minute looping run every 19
minutes on its own — nothing to keep running locally, and within each run
the dashboard-backing asset refreshes about once a minute. Adjust the loop's
`sleep 60` / cron expression in the workflow file if you want a different
cadence — check GitHub's [cron syntax docs](https://docs.github.com/actions/using-workflows/events-that-trigger-workflows#schedule).
Note that scheduled workflows are paused automatically if the repo has no
activity for 60 days, so you'll need to push a commit or manually re-enable
it if that happens.

**Local smoke test before pushing:**

```bash
uip login --client-id <ID> --client-secret <SECRET> --tenant <TENANT> --scope "OR.Assets"
cd worker
cp .env.example .env.production   # fill in ASSET_KEY / ASSET_FOLDER_PATH + any API keys
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
redirect URI `http://localhost:5173` and scope `OR.Assets.Read` (read-only —
the web app only displays the snapshot, it never writes), then fill in
`webapp/.env` (copy from `.env.example`) and `webapp/uipath.json` with that
Client ID, your org, tenant, base URL, and the folder path from Step 1
(`VITE_ASSET_FOLDER_PATH`).

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
refreshing from the Orchestrator asset every 30s, independent of anyone's
laptop.

## What changed from the original app

- `backend/app/main.py`'s `/dashboard` endpoint logic → `worker/app/worker.py`
  (`build_snapshot()`), same service modules (`market.py`, `news.py`,
  `scoring.py`, `prediction.py`, `decision.py`, `alerts.py`, `options.py`,
  `trade.py`, `sector.py`, `insight.py`, `dhan_options.py`) reused as-is.
- The `/ws` websocket heartbeat and Redis cache (`core/cache.py`) were unused
  by any service and dropped — a single Orchestrator asset is now the shared
  state instead.
- `frontend/src/App.js` (axios → `localhost:8000`) → `webapp/src/Dashboard.tsx`
  (UiPath SDK → Orchestrator Asset), same layout and colors.
- Trade engine output is now explicitly labeled "informational only" in the UI.
- Scheduling runs on GitHub Actions cron rather than an unattended UiPath
  robot or a self-managed VM/server, per your preference — see Step 2.
- Storage is an Orchestrator Text asset, not Data Fabric — Data Fabric's
  record-level API rejected the confidential-app identity in every
  configuration tested (see the architecture note near the top); Orchestrator
  Assets were confirmed working with the same identity.
