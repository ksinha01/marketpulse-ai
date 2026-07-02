def generate_insight(checklist, score):
    bullish = []
    bearish = []

    for item in checklist:
        if "Bullish" in item["signal"] or "Low Fear" in item["signal"]:
            bullish.append(item["name"])
        elif "Bearish" in item["signal"] or "High Fear" in item["signal"]:
            bearish.append(item["name"])

    if score >= 40:
        tone = "Market shows strong bullish momentum."
    elif score >= 10:
        tone = "Market is range-bound with mixed signals."
    else:
        tone = "Market is under pressure with bearish signals."

    summary = tone + " "

    if bullish:
        summary += "Strength seen in: " + ", ".join(bullish) + ". "

    if bearish:
        summary += "Risks from: " + ", ".join(bearish) + ". "

    return summary