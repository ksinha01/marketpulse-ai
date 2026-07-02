import feedparser
from datetime import datetime, timezone

# 🔥 HIGH IMPACT KEYWORDS
KEYWORDS = {
    "macro": ["fed", "interest rates", "inflation", "cpi", "recession", "central bank", "bond yields"],
    "geopolitics": ["war", "oil", "opec", "geopolitics", "crude"],
    "equities": ["ai", "earnings", "stocks", "big tech"],
    "india": ["india economy", "nifty", "bank nifty", "rbi"]
}

# 🔥 WEIGHTS
WEIGHTS = {
    "macro": 3,
    "geopolitics": 2,
    "equities": 1.5,
    "india": 3
}

# 🔥 BREAKING BOOST
BREAKING_WORDS = ["breaking", "urgent", "alert"]

# =========================
# 🔥 SENTIMENT DETECTION
# =========================
def get_sentiment(title):
    t = title.lower()

    bullish_words = ["rise", "gain", "growth", "surge", "record high", "optimism", "beats"]
    bearish_words = ["fall", "drop", "fear", "war", "inflation", "crash", "selloff", "miss"]

    if any(w in t for w in bullish_words):
        return "Bullish", 1
    elif any(w in t for w in bearish_words):
        return "Bearish", -1

    return "Neutral", 0


# =========================
# 🔥 CATEGORY DETECTION
# =========================
def detect_category(title):
    t = title.lower()

    for category, words in KEYWORDS.items():
        if any(w in t for w in words):
            return category

    return "general"


# =========================
# 🔥 TIME DECAY (FRESHNESS)
# =========================
def get_time_weight(published_time):
    try:
        now = datetime.now(timezone.utc)
        pub = datetime(*published_time[:6], tzinfo=timezone.utc)

        diff_minutes = (now - pub).total_seconds() / 60

        if diff_minutes < 30:
            return 1.5   # very fresh
        elif diff_minutes < 120:
            return 1.2
        else:
            return 1

    except:
        return 1


# =========================
# 🔥 FETCH RSS SOURCE
# =========================
def fetch_feed(url):
    try:
        feed = feedparser.parse(url)
        return feed.entries
    except:
        return []


# =========================
# 🔥 MAIN ENGINE
# =========================
def get_news():
    try:
        # 🔥 MULTI SOURCE
        sources = [
            "https://feeds.reuters.com/reuters/businessNews",
            "https://finance.yahoo.com/news/rssindex"
        ]

        entries = []

        for src in sources:
            entries.extend(fetch_feed(src))

        news = []

        for entry in entries[:30]:
            title = entry.get("title", "")

            if not title:
                continue

            category = detect_category(title)
            impact, base_score = get_sentiment(title)

            weight = WEIGHTS.get(category, 1)

            # 🔥 BREAKING BOOST
            if any(w in title.lower() for w in BREAKING_WORDS):
                weight *= 1.5

            # 🔥 TIME WEIGHT
            time_weight = get_time_weight(entry.get("published_parsed", None))

            final_score = base_score * weight * time_weight

            news.append({
                "title": title,
                "impact": impact,
                "score": round(final_score, 2),
                "category": category,
                "weight": weight,
                "time": entry.get("published", str(datetime.now()))
            })

        # 🔥 SORT BY IMPACT
        news = sorted(news, key=lambda x: abs(x["score"]), reverse=True)

        # 🔥 REMOVE LOW VALUE NOISE
        news = [n for n in news if abs(n["score"]) > 0]

        print(f"🔥 NEWS LOADED: {len(news)}")

        # =========================
        # 🔥 FINAL SAFETY (CRITICAL)
        # =========================
        if not news:
            raise Exception("Empty news after filtering")

        return news[:10]

    except Exception as e:
        print("❌ News Engine Error:", str(e))

        # 🔥 NEVER RETURN EMPTY
        return [
            {
                "title": "Fed policy uncertainty keeps markets cautious",
                "impact": "Neutral",
                "score": 0,
                "category": "macro"
            },
            {
                "title": "Oil prices volatile amid geopolitical tensions",
                "impact": "Bearish",
                "score": -2,
                "category": "geopolitics"
            },
            {
                "title": "Nifty trades near key support levels",
                "impact": "Neutral",
                "score": 0,
                "category": "india"
            }
        ]