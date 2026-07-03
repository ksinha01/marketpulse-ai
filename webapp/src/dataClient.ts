// Reads the snapshot as a plain JSON file from GitHub, NOT via the UiPath
// SDK. The UiPath Orchestrator Assets OData API doesn't send CORS headers
// for this app's origin — confirmed via browser devtools ("No
// 'Access-Control-Allow-Origin' header is present on the requested
// resource"), not assumed — so a direct browser fetch to Orchestrator is
// blocked regardless of auth/scope. raw.githubusercontent.com sends
// `Access-Control-Allow-Origin: *` on every file, sidestepping that
// entirely. The worker still writes the "official" copy to an Orchestrator
// asset too (see worker/app/asset_client.py) — this is purely a
// browser-readable mirror of the same data, committed to the repo each
// cycle by the worker's GitHub Actions job.
const SNAPSHOT_URL = 'https://cdn.jsdelivr.net/gh/ksinha01/marketpulse-ai@main/data/snapshot.json';
export interface Snapshot {
  sentiment: string;
  score: number;
  decisionText: string;
  predictionTrend: string;
  predictionConfidence: string;
  alertType: string;
  alertMessage: string;
  alertAction: string;
  tradeType: string;
  tradeReason: string;
  market: Record<string, { price: number; change: number }>;
  sectors: Record<string, number>;
  news: Array<{ title: string; impact: string }>;
  checklist: Array<{ name: string; signal: string }>;
  strategy: { strategy?: string; setup?: string; confidence?: string; reason?: string };
  insight: string;
  snapshotTime: string;
}

export async function fetchLatestSnapshot(): Promise<Snapshot | null> {
  // Cache-bust — raw.githubusercontent.com and intermediate CDNs cache
  // aggressively; without this the dashboard could show stale data well
  // past when the worker actually updated it.
  const resp = await fetch(`${SNAPSHOT_URL}?t=${Date.now()}`, { cache: 'no-store' });
  if (!resp.ok) {
    if (resp.status === 404) return null; // worker hasn't written a snapshot yet
    throw new Error(`Failed to fetch snapshot: ${resp.status}`);
  }
  return (await resp.json()) as Snapshot;
}
