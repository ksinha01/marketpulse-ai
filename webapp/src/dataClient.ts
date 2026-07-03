// Reads the snapshot as a plain JSON file from GitHub via jsDelivr's CDN
// mirror, NOT via the UiPath SDK. Confirmed via HAR file inspection: the
// Orchestrator Assets OData API sends zero Access-Control-* headers on its
// CORS preflight response, for any identity type tested (confidential app,
// interactive user) — a platform-side gap, not a config issue on our end.
//
// jsDelivr's purge API is rate-limited to roughly once every 5-7 minutes
// per file (confirmed via its own API response: "throttled": true with a
// counting-down "throttlingReset" in seconds) — calling it more often than
// that doesn't make data fresher, it just returns "finished" without
// actually invalidating anything. So the realistic effective freshness
// here is ~5-7 minutes behind the worker's actual writes, not near-real-time.
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
  const resp = await fetch(`${SNAPSHOT_URL}?t=${Date.now()}`, { cache: 'no-store' });
  if (!resp.ok) {
    if (resp.status === 404) return null; // worker hasn't written a snapshot yet
    throw new Error(`Failed to fetch snapshot: ${resp.status}`);
  }
  return (await resp.json()) as Snapshot;
}
