import random

# 🔥 GENERATE SMART OPTION CHAIN (AI-DRIVEN)
def get_option_chain(market=None, prediction=None):
    try:
        # 🔹 Get Nifty price
        nifty_price = market.get("nifty", {}).get("price", 22500)

        # 🔹 Round to nearest 50 (ATM)
        atm = round(nifty_price / 50) * 50

        strikes = [atm + i * 50 for i in range(-10, 11)]

        data = []

        trend = prediction.get("trend", "") if prediction else ""

        for i, strike in enumerate(strikes):
            distance = abs(strike - atm)

            # 🔥 BASE OI
            base_oi = max(100000 - distance * 500, 5000)

            # 🔥 TREND LOGIC
            if "UP" in trend:
                call_oi = base_oi + random.randint(5000, 15000)
                put_oi = base_oi - random.randint(2000, 8000)
            elif "DOWN" in trend:
                call_oi = base_oi - random.randint(2000, 8000)
                put_oi = base_oi + random.randint(5000, 15000)
            else:
                call_oi = base_oi
                put_oi = base_oi

            data.append({
                "strikePrice": strike,
                "CE": {
                    "openInterest": max(call_oi, 1000),
                    "changeinOpenInterest": random.randint(-2000, 5000)
                },
                "PE": {
                    "openInterest": max(put_oi, 1000),
                    "changeinOpenInterest": random.randint(-2000, 5000)
                }
            })

        print(f"✅ SMART OI GENERATED (ATM: {atm})")
        return data

    except Exception as e:
        print("❌ Smart OI Error:", str(e))
        return []


# 🔥 TOP OI
def get_top_oi(data):
    calls = []
    puts = []

    for item in data:
        strike = item["strikePrice"]

        calls.append({
            "strike": strike,
            "oi": item["CE"]["openInterest"],
            "change": item["CE"]["changeinOpenInterest"]
        })

        puts.append({
            "strike": strike,
            "oi": item["PE"]["openInterest"],
            "change": item["PE"]["changeinOpenInterest"]
        })

    return (
        sorted(calls, key=lambda x: x["oi"], reverse=True)[:10],
        sorted(puts, key=lambda x: x["oi"], reverse=True)[:10]
    )


# 🔥 PCR
def calculate_pcr(data):
    total_call = sum(d["CE"]["openInterest"] for d in data)
    total_put = sum(d["PE"]["openInterest"] for d in data)

    return round(total_put / total_call, 2) if total_call else 0


# 🔥 MAX PAIN
def calculate_max_pain(data):
    pain = {}

    for strike_data in data:
        strike = strike_data["strikePrice"]
        total = 0

        for d in data:
            diff = abs(strike - d["strikePrice"])
            total += diff * (d["CE"]["openInterest"] + d["PE"]["openInterest"])

        pain[strike] = total

    return min(pain, key=pain.get)


# 🔥 STRATEGY ENGINE (UPGRADED)
def generate_strategy(sentiment, prediction, pcr, max_pain=None):

    # 🔥 STRONG BULLISH
    if "BULLISH" in sentiment and "UP" in prediction:
        return {
            "strategy": "Bull Call Spread",
            "setup": "Buy ATM CE, Sell OTM CE",
            "confidence": "High",
            "execution": "Buy ATM Call near support",
            "reason": "Trend + sentiment aligned"
        }

    # 🔥 STRONG BEARISH
    if "BEARISH" in sentiment and "DOWN" in prediction:
        return {
            "strategy": "Bear Put Spread",
            "setup": "Buy ATM PE, Sell OTM PE",
            "confidence": "High",
            "execution": "Buy ATM Put on breakdown",
            "reason": "Downtrend confirmation"
        }

    # 🔥 SIDEWAYS
    if 0.9 <= pcr <= 1.2:
        return {
            "strategy": "Iron Condor",
            "setup": "Sell OTM CE + PE",
            "confidence": "Medium",
            "execution": "Range trading",
            "reason": "Balanced OI"
        }

    # 🔥 VOLATILE
    return {
        "strategy": "Straddle",
        "setup": "Buy CE + PE",
        "confidence": "Medium",
        "execution": "Volatility breakout",
        "reason": "Uncertain direction"
    }