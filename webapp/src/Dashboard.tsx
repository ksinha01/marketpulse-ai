import { useEffect, useState } from 'react';
import { fetchLatestSnapshot } from './dataClient';
import type { Snapshot } from './dataClient';

const POLL_MS = 30_000; // GitHub raw file read; the worker itself writes every ~1 min on its own schedule

export default function Dashboard() {
  const [data, setData] = useState<Snapshot | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const snap = await fetchLatestSnapshot();
        if (!cancelled) {
          setData(snap);
          setErr(snap ? null : 'No snapshot yet — has the worker run at least once?');
        }
      } catch (e: any) {
        if (!cancelled) setErr(e?.message ?? 'Failed to load snapshot');
      }
    };

    load();
    const interval = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (err && !data) return <div style={loadingStyle}>{err}</div>;
  if (!data) return <div style={loadingStyle}>Loading market data...</div>;

  const sentimentColor = data.sentiment?.includes('BULLISH') ? '#00c853'
    : data.sentiment?.includes('BEARISH') ? '#ff5252' : '#ffb300';

  const predictionColor = data.predictionTrend?.includes('UP') ? '#00c853'
    : data.predictionTrend?.includes('DOWN') ? '#ff5252' : '#ffb300';

  const alertColor = data.alertType?.includes('RISK') ? '#ff5252'
    : data.alertType?.includes('BULLISH') ? '#00c853' : '#ffb300';

  const bullishNews = data.news?.filter(n => n.impact?.includes('Bullish')).length || 0;
  const bearishNews = data.news?.filter(n => n.impact?.includes('Bearish')).length || 0;

  const strategy = data.strategy || {};
  const strategyColor = strategy.confidence === 'High' ? '#00c853'
    : strategy.confidence === 'Medium' ? '#ffb300' : '#ff5252';

  return (
    <div style={container}>
      <div style={header}>
        <h2>MarketPulse</h2>
        <div style={{ fontSize: '11px', color: '#666' }}>
          Last updated: {data.snapshotTime ? new Date(data.snapshotTime).toLocaleString() : '—'}
        </div>
      </div>

      {data.alertType && (
        <div style={{ ...alertBox, borderLeft: `4px solid ${alertColor}` }}>
          <strong>{data.alertType}</strong>
          <div style={{ fontSize: '12px', color: '#aaa' }}>{data.alertMessage}</div>
          <div style={{ fontSize: '11px', color: '#888' }}>👉 {data.alertAction}</div>
        </div>
      )}

      <div style={topStrip}>
        <Card title="Prediction" value={data.predictionTrend} color={predictionColor} sub={data.predictionConfidence} />
        <Card title="Sentiment" value={data.sentiment} color={sentimentColor} sub={`Score: ${data.score}`} />
        <Card title="News" value={`🟢 ${bullishNews} / 🔴 ${bearishNews}`} />
      </div>

      {data.decisionText && (
        <div style={{ background: '#111', padding: '12px', borderRadius: '6px', marginTop: '10px', borderLeft: '4px solid #ffb300' }}>
          <strong>{data.decisionText}</strong>
        </div>
      )}

      <div style={strategyBox}>
        <h4>⚡ Strategy</h4>
        {strategy.strategy ? (
          <>
            <div style={{ fontSize: '16px', color: '#00c853', fontWeight: 600 }}>{strategy.strategy}</div>
            <div style={{ fontSize: '12px', color: '#aaa', marginTop: '4px' }}>{strategy.setup}</div>
            <div style={{ marginTop: '6px', fontSize: '12px', color: strategyColor }}>
              Confidence: {strategy.confidence}
            </div>
            <div style={{ fontSize: '11px', color: '#777', marginTop: '4px' }}>{strategy.reason}</div>
          </>
        ) : (
          <div style={{ color: '#777', fontSize: '12px' }}>No strategy available</div>
        )}
      </div>

      {/* NOTE: analysis/signal display only — this dashboard does not place trades. */}
      {data.tradeType && data.tradeType !== 'NO TRADE' && (
        <div style={{ background: '#111', padding: '10px', borderRadius: '6px', marginTop: '10px', border: '1px solid #222' }}>
          <div style={{ fontSize: '12px', color: '#888' }}>Trade Signal (informational only)</div>
          <div style={{ fontSize: '14px' }}>{data.tradeType}</div>
          <div style={{ fontSize: '11px', color: '#777' }}>{data.tradeReason}</div>
        </div>
      )}

      <div style={marketStrip}>
        {Object.entries(data.market || {}).map(([key, val]: any, i) => {
          const change = val?.change || 0;
          return (
            <div key={i} style={ticker}>
              <div style={tickerName}>{key.toUpperCase()}</div>
              <div>{val?.price}</div>
              <div style={{ color: change > 0 ? '#00c853' : '#ff5252' }}>
                {change > 0 ? '+' : ''}{change}%
              </div>
            </div>
          );
        })}
      </div>

      <div style={grid}>
        <div style={card}>
          <h4>Checklist</h4>
          {data.checklist?.map((item, i) => (
            <div key={i} style={row}>
              <span>{item.name}</span>
              <span style={{
                color: item.signal?.includes('Bullish') ? '#00c853'
                  : item.signal?.includes('Bearish') ? '#ff5252' : '#ffb300',
              }}>
                {item.signal}
              </span>
            </div>
          ))}
        </div>

        <div style={card}>
          <h4>Insight</h4>
          <p style={{ fontSize: '13px', color: '#aaa' }}>{data.insight || 'No insight available'}</p>
        </div>

        <div style={card}>
          <h4>Sectors</h4>
          <div style={heatmap}>
            {Object.entries(data.sectors || {}).map(([k, v]: any, i) => (
              <div key={i} style={{
                padding: '6px', borderRadius: '4px', background: '#0b0e11',
                color: v > 0 ? '#00c853' : '#ff5252', fontSize: '12px',
              }}>
                {k}: {v > 0 ? '+' : ''}{v}%
              </div>
            ))}
          </div>
        </div>

        <div style={card}>
          <h4>News</h4>
          {data.news && data.news.length > 0 ? (
            data.news.map((n, i) => {
              const color = n.impact?.includes('Bullish') ? '#00c853'
                : n.impact?.includes('Bearish') ? '#ff5252' : '#ffb300';
              return (
                <div key={i} style={newsRow}>
                  <span style={{ width: '80%' }}>{n.title}</span>
                  <span style={{ color, fontSize: '11px' }}>{n.impact}</span>
                </div>
              );
            })
          ) : (
            <div style={{ color: '#888', fontSize: '12px' }}>No high-impact news right now</div>
          )}
        </div>
      </div>
    </div>
  );
}

const Card = ({ title, value, color, sub }: { title: string; value?: string; color?: string; sub?: string }) => (
  <div style={miniCard}>
    <div style={{ fontSize: '12px', color: '#888' }}>{title}</div>
    <div style={{ fontSize: '18px', color }}>{value}</div>
    {sub && <div style={{ fontSize: '11px', color: '#aaa' }}>{sub}</div>}
  </div>
);

const container: React.CSSProperties = { background: '#0b0e11', color: '#e6edf3', minHeight: '100vh', fontFamily: 'system-ui', padding: '10px' };
const header: React.CSSProperties = { padding: '10px 0', borderBottom: '1px solid #222', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' };
const alertBox: React.CSSProperties = { background: '#111', padding: '10px', borderRadius: '6px', marginTop: '10px' };
const strategyBox: React.CSSProperties = { background: '#111', padding: '12px', borderRadius: '6px', marginTop: '10px', border: '1px solid #222' };
const topStrip: React.CSSProperties = { display: 'flex', gap: '10px', marginTop: '10px' };
const miniCard: React.CSSProperties = { flex: 1, background: '#111', padding: '10px', borderRadius: '6px' };
const marketStrip: React.CSSProperties = { display: 'flex', overflowX: 'auto', gap: '10px', marginTop: '10px' };
const ticker: React.CSSProperties = { background: '#111', padding: '10px', borderRadius: '6px', minWidth: '100px' };
const tickerName: React.CSSProperties = { fontSize: '11px', color: '#888' };
const grid: React.CSSProperties = { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '10px' };
const card: React.CSSProperties = { background: '#111', padding: '10px', borderRadius: '6px' };
const row: React.CSSProperties = { display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '5px' };
const newsRow: React.CSSProperties = { fontSize: '12px', marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' };
const heatmap: React.CSSProperties = { display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px' };
const loadingStyle: React.CSSProperties = { color: '#0b0e11', background: '#fff', padding: '20px', fontFamily: 'system-ui', minHeight: '100vh' };
