import requests
import math
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/"
}


# =========================
# 🔥 NSE FETCH (REAL DATA)
# =========================
def fetch_nse_all():
    try:
        session = requests.Session()

        # Step 1: get cookies
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=5)
        time.sleep(1)

        # Step 2: fetch indices
        url = "https://www.nseindia.com/api/allIndices"
        res = session.get(url, headers=HEADERS, timeout=10)

        if res.status_code != 200:
            print("❌ NSE blocked")
            return {}

        data = res.json().get("data", [])

        result = {}

        for item in data:
            name = item.get("index")

            if name == "NIFTY 50":
                result["nifty"] = {
                    "price": item.get("last", 0),
                    "change": item.get("percentChange", 0)
                }

            elif name == "NIFTY BANK":
                result["banknifty"] = {
                    "price": item.get("last", 0),
                    "change": item.get("percentChange", 0)
                }

            elif name == "NIFTY FINANCIAL SERVICES":
                result["finnifty"] = {
                    "price": item.get("last", 0),
                    "change": item.get("percentChange", 0)
                }

            elif name == "INDIA VIX":
                result["indiavix"] = {
                    "price": item.get("last", 0),
                    "change": item.get("percentChange", 0)
                }

        return result

    except Exception as e:
        print("NSE Error:", str(e))
        return {}


# =========================
# 🔹 GLOBAL (KEEP YAHOO ONLY HERE)
# =========================
import yfinance as yf

def fetch_yf(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1d")

        if data.empty:
            return {"price": 0, "change": 0}

        close = float(data["Close"].iloc[-1])
        open_price = float(data["Open"].iloc[-1])

        change = ((close - open_price) / open_price) * 100 if open_price else 0

        if not math.isfinite(change):
            change = 0
        if not math.isfinite(close):
            close = 0

        return {"price": round(close, 2), "change": round(change, 2)}

    except:
        return {"price": 0, "change": 0}


# =========================
# 🔥 MAIN FUNCTION
# =========================
def get_market_data():

    # 🔹 GLOBAL (safe)
    sp500 = fetch_yf("^GSPC")
    nasdaq = fetch_yf("^IXIC")
    vix = fetch_yf("^VIX")
    usd_inr = fetch_yf("INR=X")
    us10y = fetch_yf("^TNX")

    # 🔥 INDIA (REAL NSE)
    nse = fetch_nse_all()

    nifty = nse.get("nifty", {"price": 0, "change": 0})
    banknifty = nse.get("banknifty", {"price": 0, "change": 0})
    finnifty = nse.get("finnifty", {"price": 0, "change": 0})
    indiavix = nse.get("indiavix", {"price": 0, "change": 0})

    # 🔥 GIFT NIFTY (proxy — unavoidable)
    gift_change = (
        sp500["change"] * 0.4 +
        nasdaq["change"] * 0.4 +
        vix["change"] * -0.2
    )

    gift_nifty = {
        "price": nifty["price"],
        "change": round(gift_change, 2)
    }

    return {
        "sp500": sp500,
        "nasdaq": nasdaq,
        "vix": vix,
        "usd_inr": usd_inr,
        "us10y": us10y,
        "nifty": nifty,          # ✅ FIXED
        "banknifty": banknifty,  # ✅ FIXED
        "finnifty": finnifty,    # ✅ REAL
        "indiavix": indiavix,    # ✅ REAL
        "gift_nifty": gift_nifty
    }