def generate_trade(market, prediction, sentiment):
    try:
        nifty = market.get("nifty", {}).get("price", 0)
        change = market.get("nifty", {}).get("change", 0)

        if nifty == 0:
            return {
                "type": "NO TRADE",
                "reason": "Nifty data unavailable"
            }

        # 🔥 ATM STRIKE (ROUND TO 50)
        atm = round(nifty / 50) * 50

        # =========================
        # 🔹 CALL TRADE
        # =========================
        if "UP" in prediction and "BULLISH" in sentiment:
            return {
                "type": "CALL",
                "strike": atm,
                "entry": round(atm * 0.01, 2),   # mock premium
                "sl": round(atm * 0.008, 2),
                "target": round(atm * 0.015, 2),
                "rr": "1:2",
                "reason": "Bullish trend + gap up"
            }

        # =========================
        # 🔹 PUT TRADE
        # =========================
        elif "DOWN" in prediction and "BEARISH" in sentiment:
            return {
                "type": "PUT",
                "strike": atm,
                "entry": round(atm * 0.01, 2),
                "sl": round(atm * 0.008, 2),
                "target": round(atm * 0.015, 2),
                "rr": "1:2",
                "reason": "Bearish trend + gap down"
            }

        # =========================
        # 🔹 NO TRADE
        # =========================
        else:
            return {
                "type": "NO TRADE",
                "reason": "No clear confirmation"
            }

    except Exception as e:
        print("Trade Engine Error:", str(e))
        return {
            "type": "ERROR",
            "reason": "Trade calculation failed"
        }