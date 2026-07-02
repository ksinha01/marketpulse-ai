def generate_alert(news, prediction):
    try:
        bullish = 0
        bearish = 0

        for n in news or []:
            impact = n.get("impact", "")

            if "Bullish" in impact:
                bullish += 1
            elif "Bearish" in impact:
                bearish += 1

        trend = prediction.get("trend", "")

        # 🔴 STRONG BEARISH
        if bearish >= 3 and "DOWN" in trend:
            return {
                "type": "🚨 HIGH RISK",
                "message": "Bearish news spike + Gap Down expected",
                "action": "Avoid longs / consider hedging"
            }

        # 🟢 STRONG BULLISH
        elif bullish >= 3 and "UP" in trend:
            return {
                "type": "🚀 STRONG BULLISH",
                "message": "Bullish news + Gap Up expected",
                "action": "Look for buying opportunities"
            }

        # ⚠️ MIXED SIGNAL
        elif (bullish > bearish and "DOWN" in trend) or (bearish > bullish and "UP" in trend):
            return {
                "type": "⚠️ MIXED SIGNAL",
                "message": "News and prediction are conflicting",
                "action": "Trade cautiously"
            }

        # 🟡 NEUTRAL
        else:
            return {
                "type": "🟡 NEUTRAL",
                "message": "No strong edge",
                "action": "Wait for clear setup"
            }

    except Exception as e:
        print("Alert Error:", str(e))
        return {
            "type": "Error",
            "message": "Alert failed",
            "action": "N/A"
        }