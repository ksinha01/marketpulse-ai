import { Entities } from '@uipath/uipath-typescript/entities';
import type { EntityRecord } from '@uipath/uipath-typescript/entities';
import type { UiPath } from '@uipath/uipath-typescript/core';

const ENTITY_ID = import.meta.env.VITE_DF_ENTITY_ID as string;

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
 * Reads the single upserted snapshot row the worker maintains.
 * pageSize: 1 is always "the latest" because the worker writes one fixed row.
 */
export async function fetchLatestSnapshot(sdk: UiPath): Promise<Snapshot | null> {
  const entities = new Entities(sdk);
  const result: any = await entities.getAllRecords(ENTITY_ID, { pageSize: 1 } as any);
  const items: EntityRecord[] = result?.items ?? result ?? [];
  const row: any = items[0];
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
