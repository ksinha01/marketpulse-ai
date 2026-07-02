from dhanhq import dhanhq
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

client_id = os.getenv("DHAN_CLIENT_ID")
access_token = os.getenv("DHAN_ACCESS_TOKEN")

dhan = dhanhq(client_id, access_token)


# 🔥 AUTO GET NEAREST EXPIRY (THURSDAY)
def get_nearest_expiry():
    today = datetime.today()

    # Thursday = 3
    days_ahead = 3 - today.weekday()

    if days_ahead <= 0:
        days_ahead += 7

    expiry = today + timedelta(days=days_ahead)
    return expiry.strftime("%Y-%m-%d")


# 🔥 FETCH OPTION CHAIN (FIXED)
def get_option_chain(symbol="NIFTY"):
    try:
        if symbol == "NIFTY":
            security_id = 13
        elif symbol == "BANKNIFTY":
            security_id = 25
        else:
            return []

        expiry = get_nearest_expiry()

        print(f"🔍 Fetching: {symbol}, Expiry: {expiry}")

        res = dhan.option_chain(
            under_security_id=security_id,
            under_exchange_segment="IDX",
            expiry=expiry
        )

        # 🔥 FULL DEBUG
        print("📦 RAW DHAN:", res)

        if not res or res.get("status") == "failed":
            print("❌ Dhan API failed")
            return []

        raw = res.get("data")

        # =========================
        # ❌ CASE: STRING RESPONSE
        # =========================
        if isinstance(raw, str):
            print("❌ Dhan returned string:", raw)
            return []

        # =========================
        # ❌ CASE: EMPTY
        # =========================
        if not raw:
            print("⚠️ Empty Dhan data")
            return []

        normalized = []

        # =========================
        # ✅ CASE: LIST FORMAT
        # =========================
        if isinstance(raw, list):
            for item in raw:
                normalized.append({
                    "strikePrice": item.get("strikePrice"),
                    "CE": {
                        "openInterest": item.get("callOptions", {}).get("openInterest", 0),
                        "changeinOpenInterest": item.get("callOptions", {}).get("changeInOI", 0)
                    },
                    "PE": {
                        "openInterest": item.get("putOptions", {}).get("openInterest", 0),
                        "changeinOpenInterest": item.get("putOptions", {}).get("changeInOI", 0)
                    }
                })

        else:
            print("⚠️ Unknown structure:", type(raw))
            return []

        print(f"✅ DHAN WORKING ({len(normalized)} strikes)")
        return normalized

    except Exception as e:
        print("❌ Dhan Error:", str(e))
        return []
# 🔥 TOP OI
def get_top_oi(data):
    calls, puts = [], []

    for item in data:
        strike = item.get("strikePrice")

        ce = item.get("callOptions", {})
        pe = item.get("putOptions", {})

        calls.append({
            "strike": strike,
            "oi": ce.get("openInterest", 0),
            "change": ce.get("changeInOI", 0)
        })

        puts.append({
            "strike": strike,
            "oi": pe.get("openInterest", 0),
            "change": pe.get("changeInOI", 0)
        })

    return (
        sorted(calls, key=lambda x: x["oi"], reverse=True)[:10],
        sorted(puts, key=lambda x: x["oi"], reverse=True)[:10]
    )


# 🔥 PCR
def calculate_pcr(data):
    total_call = sum(item.get("callOptions", {}).get("openInterest", 0) for item in data)
    total_put = sum(item.get("putOptions", {}).get("openInterest", 0) for item in data)

    return round(total_put / total_call, 2) if total_call else 0


# 🔥 MAX PAIN
def calculate_max_pain(data):
    if not data:
        return 0

    strikes = [item.get("strikePrice") for item in data]

    pain = {}

    for strike in strikes:
        total = 0

        for item in data:
            diff = abs(strike - item.get("strikePrice", 0))

            ce = item.get("callOptions", {}).get("openInterest", 0)
            pe = item.get("putOptions", {}).get("openInterest", 0)

            total += diff * (ce + pe)

        pain[strike] = total

    return min(pain, key=pain.get) if pain else 0


# 🔥 STRATEGY ENGINE
def generate_strategy(sentiment, prediction, pcr, max_pain=None):

    if "STRONG BULLISH" in sentiment or "GAP UP" in prediction:
        return {
            "strategy": "Bull Call Spread",
            "setup": "Buy ATM CE, Sell OTM CE",
            "confidence": "High",
            "reason": "Bullish momentum"
        }

    if "BEARISH" in sentiment or "GAP DOWN" in prediction:
        return {
            "strategy": "Bear Put Spread",
            "setup": "Buy ATM PE, Sell OTM PE",
            "confidence": "High",
            "reason": "Downtrend expected"
        }

    if 0.9 <= pcr <= 1.2:
        return {
            "strategy": "Iron Condor",
            "setup": "Range market",
            "confidence": "Medium",
            "reason": "Neutral PCR"
        }

    return {
        "strategy": "Straddle",
        "setup": "Volatility play",
        "confidence": "Medium",
        "reason": "Uncertain direction"
    }