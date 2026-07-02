def predict_market(market, news_score=0):
    try:
        gift = market.get("gift_nifty", {}).get("change", 0)
        sp500 = market.get("sp500", {}).get("change", 0)
        nasdaq = market.get("nasdaq", {}).get("change", 0)
        vix = market.get("vix", {}).get("price", 15)

        score = 0
        reasons = []

        # 🔹 GIFT NIFTY (Highest weight)
        if gift > 0.3:
            score += 50
            reasons.append("GIFT Nifty strong")
        elif gift < -0.3:
            score -= 40
            reasons.append("GIFT Nifty weak")

        # 🔹 US MARKETS
        if sp500 > 0.3:
            score += 20
            reasons.append("S&P 500 positive")
        elif sp500 < -0.3:
            score -= 20
            reasons.append("S&P 500 weak")

        if nasdaq > 0.5:
            score += 20
            reasons.append("Nasdaq strong")
        elif nasdaq < -0.5:
            score -= 20
            reasons.append("Nasdaq weak")

        # 🔹 VIX (fear gauge)
        if vix > 18:
            score -= 15
            reasons.append("High VIX (fear)")
        elif vix < 14:
            score += 10
            reasons.append("Low VIX (confidence)")

        # 🔥 NEWS IMPACT (NEW)
        if news_score != 0:
            score += news_score
            if news_score > 2:
                reasons.append("Positive global news flow")
            elif news_score < -2:
                reasons.append("Negative global news flow")

        # 🔥 SIGNAL NORMALIZATION
        # Prevent extreme over-weighting
        if score > 100:
            score = 100
        elif score < -100:
            score = -100

        # 🔥 FINAL DECISION
        if score >= 50:
            trend = "📈 STRONG GAP UP"
            confidence = "High"
        elif score >= 20:
            trend = "📈 GAP UP"
            confidence = "Medium"
        elif score > -10:
            trend = "🟡 SIDEWAYS"
            confidence = "Low"
        elif score > -40:
            trend = "📉 GAP DOWN"
            confidence = "Medium"
        else:
            trend = "📉 STRONG GAP DOWN"
            confidence = "High"

        return {
            "trend": trend,
            "confidence": confidence,
            "score": score,
            "reason": ", ".join(reasons) if reasons else "Mixed signals"
        }

    except Exception as e:
        print("Prediction Error:", str(e))
        return {
            "trend": "Unknown",
            "confidence": "Low",
            "score": 0,
            "reason": "Error in prediction"
        }