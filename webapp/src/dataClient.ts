// Reads the snapshot through a Cloudflare Worker proxy, NOT directly from
// GitHub or the UiPath SDK. Two things this works around:
//   1. UiPath's Orchestrator Assets OData API sends zero CORS headers on
//      preflight, for any identity type — confirmed via HAR inspection.
//   2. raw.githubusercontent.com and jsDelivr both cache responses for
//      several minutes regardless of cache-busting query params or purge
//      calls (jsDelivr's purge is itself throttled to ~5-7 min).
// The Worker proxies GitHub's live Contents API instead (not the cached
// raw-file CDN), with Cache-Control: no-store, giving genuinely fresh data
// within seconds of the worker's actual writes. See /cloudflare-worker in
// the repo for the proxy's own source and setup steps.
const SNAPSHOT_URL = 'https://marketpulse-proxy.marketpulse-ai.workers.dev';

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
