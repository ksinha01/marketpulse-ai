def final_decision(sentiment, prediction):
    try:
        decision = {}
        
        # =========================
        # 🔥 ALIGNMENT CASE
        # =========================
        if "BULLISH" in sentiment and "UP" in prediction:
            decision = {
                "signal": "STRONG BUY",
                "type": "CONFIRMED",
                "message": "Global + Intraday aligned bullish",
                "action": "Buy Calls aggressively"
            }

        elif "BEARISH" in sentiment and "DOWN" in prediction:
            decision = {
                "signal": "STRONG SELL",
                "type": "CONFIRMED",
                "message": "Global + Intraday aligned bearish",
                "action": "Buy Puts aggressively"
            }

        # =========================
        # 🔥 CONFLICT CASE (IMPORTANT)
        # =========================
        elif "DOWN" in prediction and "BULLISH" in sentiment:
            decision = {
                "signal": "REVERSAL ALERT",
                "type": "SMART MONEY",
                "message": "Gap down but buying seen (possible reversal)",
                "action": "Wait for dip buying / avoid early shorts"
            }

        elif "UP" in prediction and "BEARISH" in sentiment:
            decision = {
                "signal": "FAKE BREAKOUT",
                "type": "TRAP",
                "message": "Gap up but selling pressure",
                "action": "Avoid longs / look for shorting"
            }

        # =========================
        # 🔥 DEFAULT
        # =========================
        else:
            decision = {
                "signal": "NO EDGE",
                "type": "NEUTRAL",
                "message": "No clear setup",
                "action": "Wait"
            }

        return decision

    except Exception as e:
        print("Decision Error:", str(e))
        return {}