def calculate_sentiment(data, news):
    score = 0
    checklist = []

    # 🔹 HELPERS
    def get_change(key):
        return data.get(key, {}).get("change", 0)

    def get_price(key, default=15):
        return data.get(key, {}).get("price", default)

    nifty = get_change("nifty")
    banknifty = get_change("banknifty")
    finnifty = get_change("finnifty")
    vix = get_price("vix")

    # =========================
    # 🔥 1. NIFTY CORE ENGINE
    # =========================

    if nifty > 1:
        score += 40
        checklist.append({"name": "Nifty Trend", "signal": "Strong Bullish Breakout"})
    elif nifty > 0.4:
        score += 25
        checklist.append({"name": "Nifty Trend", "signal": "Bullish"})
    elif nifty < -1:
        score -= 40
        checklist.append({"name": "Nifty Trend", "signal": "Strong Bearish Breakdown"})
    elif nifty < -0.4:
        score -= 25
        checklist.append({"name": "Nifty Trend", "signal": "Bearish"})
    else:
        checklist.append({"name": "Nifty Trend", "signal": "Sideways"})

    # =========================
    # 🔥 2. BANKNIFTY CONFIRMATION
    # =========================

    if banknifty > 1:
        score += 20
        checklist.append({"name": "BankNifty", "signal": "Strong Support"})
    elif banknifty < -1:
        score -= 20
        checklist.append({"name": "BankNifty", "signal": "Strong Weakness"})
    else:
        checklist.append({"name": "BankNifty", "signal": "Neutral"})

    # =========================
    # 🔥 3. FINNIFTY (SMART MONEY)
    # =========================

    if finnifty > 0.7:
        score += 15
        checklist.append({"name": "FinNifty", "signal": "Institutional Buying"})
    elif finnifty < -0.7:
        score -= 15
        checklist.append({"name": "FinNifty", "signal": "Institutional Selling"})
    else:
        checklist.append({"name": "FinNifty", "signal": "Neutral"})

    # =========================
    # 🔥 4. MOMENTUM ALIGNMENT
    # =========================

    if nifty > 0 and banknifty > 0 and finnifty > 0:
        score += 20
        checklist.append({"name": "Momentum", "signal": "Strong Bullish Alignment"})
    elif nifty < 0 and banknifty < 0 and finnifty < 0:
        score -= 20
        checklist.append({"name": "Momentum", "signal": "Strong Bearish Alignment"})
    else:
        score -= 10
        checklist.append({"name": "Momentum", "signal": "Divergence (Caution)"})

    # =========================
    # 🔥 5. TRAP DETECTION
    # =========================

    if abs(nifty) > 0.8 and abs(banknifty) < 0.3:
        score -= 15
        checklist.append({"name": "Trap", "signal": "Nifty Move Not Supported by Banks"})

    if nifty > 0 and finnifty < 0:
        score -= 10
        checklist.append({"name": "Trap", "signal": "Retail Rally (No Smart Money)"})

    # =========================
    # 🔹 6. VOLATILITY FILTER
    # =========================

    if vix > 18:
        score -= 15
        checklist.append({"name": "VIX", "signal": "High Risk"})
    elif vix < 14:
        score += 10
        checklist.append({"name": "VIX", "signal": "Low Volatility"})
    else:
        checklist.append({"name": "VIX", "signal": "Normal"})

    # =========================
    # 🔹 7. GLOBAL SUPPORT
    # =========================

    sp500 = get_change("sp500")
    nasdaq = get_change("nasdaq")

    if sp500 > 0.5:
        score += 10
    elif sp500 < -0.5:
        score -= 10

    if nasdaq > 0.7:
        score += 10
    elif nasdaq < -0.7:
        score -= 10

    if sp500 > 0 and nasdaq > 0:
        checklist.append({"name": "Global Cues", "signal": "Bullish Support"})
    elif sp500 < 0 and nasdaq < 0:
        checklist.append({"name": "Global Cues", "signal": "Bearish Pressure"})
    else:
        checklist.append({"name": "Global Cues", "signal": "Mixed"})

    # =========================
    # 🔥 8. HIGH IMPACT NEWS ENGINE
    # =========================

    news_score = 0
    high_impact_count = 0

    for n in news or []:
        base = n.get("score", 0)
        category = n.get("category", "general")

        # 🔥 CATEGORY WEIGHTING
        if category in ["macro", "india"]:
            weighted = base * 1.5   # Fed / RBI / Nifty
        elif category == "geopolitics":
            weighted = base * 1.2   # oil / war
        else:
            weighted = base         # normal

        news_score += weighted

        # 🔥 TRACK BIG EVENTS
        if abs(weighted) >= 2:
            high_impact_count += 1

    # 🔥 DYNAMIC CAP (SMART)
    if high_impact_count >= 3:
        news_score = max(min(news_score, 30), -30)
    else:
        news_score = max(min(news_score, 20), -20)

    score += news_score

    checklist.append({
        "name": "High Impact News",
        "signal": f"Score: {round(news_score,2)} | Events: {high_impact_count}"
    })

    # =========================
    # 🔥 FINAL SENTIMENT
    # =========================

    if score >= 70:
        sentiment = "🟢 STRONG BULLISH (TREND DAY)"
    elif score >= 40:
        sentiment = "🟢 BULLISH"
    elif score >= 10:
        sentiment = "🟡 SIDEWAYS"
    elif score >= -10:
        sentiment = "🟠 WEAK BEARISH"
    else:
        sentiment = "🔴 STRONG BEARISH (TREND DAY)"

    return sentiment, score, checklist