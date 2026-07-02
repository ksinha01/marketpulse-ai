"""
MarketPulse worker — one refresh cycle.

This replaces `uvicorn`/`npm start` as the "always on" piece. It does NOT run
its own infinite loop; instead it's designed to be triggered on a schedule by
UiPath Orchestrator (Time trigger, e.g. every 5 minutes during market hours),
so "24/7" is delivered by the Orchestrator trigger + unattended robot/runtime,
not by a long-lived process you have to babysit.

Local test:
    python -m app.worker

Deploy as a UiPath scheduled unattended automation (see ../README.md).
"""
import json
import os
import traceback
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Load config from a file next to this worker instead of Orchestrator Assets.
# Resolution order: MARKETPULSE_ENV_FILE env var (if the robot sets one) ->
# .env.production next to this file -> .env next to this file.
_here = Path(__file__).resolve().parent.parent  # worker/
_env_file = os.environ.get("MARKETPULSE_ENV_FILE") or (
    str(_here / ".env.production") if (_here / ".env.production").exists() else str(_here / ".env")
)
load_dotenv(_env_file)

from app.services.market import get_market_data
from app.services.news import get_news
from app.services.insight import generate_insight
from app.services.sector import get_sector_heatmap
from app.services.prediction import predict_market
from app.services.scoring import calculate_sentiment
from app.services.alerts import generate_alert
from app.services.decision import final_decision
from app.services.trade import generate_trade
from app.services.options import (
    get_option_chain,
    get_top_oi,
    calculate_pcr,
    calculate_max_pain,
    generate_strategy,
)
from app.asset_client import upsert_snapshot

REQUIRED_MARKET_KEYS = ["nifty", "banknifty", "finnifty", "indiavix", "gift_nifty"]


def build_snapshot() -> dict:
    market = get_market_data() or {}
    for key in REQUIRED_MARKET_KEYS:
        if not market.get(key):
            market[key] = {"price": 0, "change": 0}

    news = get_news() or []

    try:
        sectors = get_sector_heatmap() or {}
    except Exception as e:
        print("Sector Error:", e)
        sectors = {}
    if not sectors:
        sectors = {"IT": 0, "PHARMA": 0, "AUTO": 0, "FMCG": 0, "METAL": 0, "ENERGY": 0}
    market["sectors"] = sectors

    sentiment, score, checklist = calculate_sentiment(market, news)
    insight = generate_insight(checklist, score)
    prediction = predict_market(market)
    decision = final_decision(sentiment, prediction.get("trend", ""))
    alert = generate_alert(news, prediction)

    top_calls, top_puts, pcr, max_pain, strategy = [], [], 0, 0, {}
    try:
        option_data = get_option_chain(market, prediction) or []
        if option_data:
            top_calls, top_puts = get_top_oi(option_data)
            pcr = calculate_pcr(option_data)
            max_pain = calculate_max_pain(option_data)
            strategy = generate_strategy(sentiment, prediction.get("trend", ""), pcr, max_pain)
    except Exception as e:
        print("Option Chain Error:", e)

    # NOTE: analysis/signal only — this does not place orders. Keep it that way
    # unless a live order-placement path is explicitly designed, reviewed, and
    # gated behind its own explicit approval step.
    trade = {"type": "NO TRADE", "reason": "Not generated"}
    try:
        trade = generate_trade(market, prediction.get("trend", ""), sentiment) or trade
    except Exception as e:
        print("Trade Error:", e)
        trade = {"type": "ERROR", "reason": "Execution failed"}

    return {
        "Sentiment": sentiment,
        "Score": score,
        "DecisionText": decision,
        "PredictionTrend": prediction.get("trend", ""),
        "PredictionConfidence": prediction.get("confidence", ""),
        "AlertType": (alert or {}).get("type", ""),
        "AlertMessage": (alert or {}).get("message", ""),
        "AlertAction": (alert or {}).get("action", ""),
        "StrategyConfidence": (strategy or {}).get("confidence", ""),
        "Pcr": pcr,
        "MaxPain": max_pain,
        "TradeType": trade.get("type", ""),
        "TradeReason": trade.get("reason", ""),
        "MarketJson": json.dumps(market),
        "SectorsJson": json.dumps(sectors),
        "NewsJson": json.dumps(news),
        "ChecklistJson": json.dumps(checklist),
        "OptionsJson": json.dumps({"calls": top_calls, "puts": top_puts, "pcr": pcr, "max_pain": max_pain}),
        "StrategyJson": json.dumps(strategy),
        "InsightText": insight,
        "SnapshotTime": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    try:
        snapshot = build_snapshot()
        upsert_snapshot(snapshot)
        print(f"✅ Snapshot written at {snapshot['SnapshotTime']}")
        return 0
    except Exception:
        print("❌ Worker run failed:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
