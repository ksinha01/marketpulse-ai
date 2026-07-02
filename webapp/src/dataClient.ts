import { Assets } from '@uipath/uipath-typescript/assets';
import type { UiPath } from '@uipath/uipath-typescript/core';

const ASSET_NAME = 'MarketPulseSnapshot';
const ASSET_FOLDER_PATH = (import.meta.env.VITE_ASSET_FOLDER_PATH as string) || 'Shared';

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

function safeParse<T>(raw: unknown, fallback: T): T {
  if (typeof raw !== 'string' || !raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

/**
 * Reads the single MarketPulseSnapshot Orchestrator asset. The worker always
 * overwrites this one asset's value with the full snapshot as a JSON string
 * (with several fields — MarketJson, NewsJson, etc. — being JSON-encoded
 * strings themselves, hence the double JSON.parse below).
 *
 * Data Fabric was the original design here, but its record-level API
 * rejected the worker's confidential-app identity outright ("unsupported
 * robot type") in every configuration tested — a Data-Fabric-specific
 * platform behavior, confirmed by direct testing (correct scopes, correct
 * entity permissions, IP restriction confirmed disabled). The identical
 * identity works fine against Orchestrator Assets, so the whole snapshot
 * lives in one asset instead of a Data Fabric entity row.
 */
export async function fetchLatestSnapshot(sdk: UiPath): Promise<Snapshot | null> {
  const assets = new Assets(sdk);
  const asset: any = await assets.getByName(ASSET_NAME, { folderPath: ASSET_FOLDER_PATH });

  // Field casing from the SDK response isn't 100% confirmed against the raw
  // Orchestrator API's PascalCase (StringValue) — trying the likely SDK
  // camelCase form first, falling back to PascalCase if that's actually
  // what comes back. If both come back undefined, this needs a console.log
  // of the raw `asset` object to see its real shape.
  const raw: string | undefined = asset?.stringValue ?? asset?.StringValue ?? asset?.value ?? asset?.Value;
  if (!raw) return null;

  const row = safeParse<any>(raw, null);
  if (!row) return null;

  return {
    sentiment: row.Sentiment ?? '',
    score: row.Score ?? 0,
    decisionText: row.DecisionText ?? '',
    predictionTrend: row.PredictionTrend ?? '',
    predictionConfidence: row.PredictionConfidence ?? '',
    alertType: row.AlertType ?? '',
    alertMessage: row.AlertMessage ?? '',
    alertAction: row.AlertAction ?? '',
    tradeType: row.TradeType ?? '',
    tradeReason: row.TradeReason ?? '',
    market: safeParse(row.MarketJson, {}),
    sectors: safeParse(row.SectorsJson, {}),
    news: safeParse(row.NewsJson, []),
    checklist: safeParse(row.ChecklistJson, []),
    strategy: safeParse(row.StrategyJson, {}),
    insight: row.InsightText ?? '',
    snapshotTime: row.SnapshotTime ?? '',
  };
}
