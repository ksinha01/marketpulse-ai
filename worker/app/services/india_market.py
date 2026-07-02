import requests

URL = "https://scanner.tradingview.com/india/scan"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}


def fetch_india_indices():
    try:
        payload = {
            "symbols": {
                "tickers": [
                    "NSE:NIFTY",
                    "NSE:BANKNIFTY",
                    "NSE:FINNIFTY",   # ✅ ADDED
                    "NSE:INDIAVIX"
                ],
                "query": {"types": []}
            },
            "columns": ["close", "change"]
        }

        res = requests.post(URL, json=payload, headers=HEADERS, timeout=10)
        data_json = res.json()

        data = {}

        for item in data_json.get("data", []):
            symbol = item.get("s", "")
            values = item.get("d", [])

            if len(values) < 2:
                continue

            price = values[0]
            change = values[1]

            # ✅ EXACT SYMBOL MATCH (NO BUGS)
            if symbol == "NSE:NIFTY":
                data["nifty"] = {"price": price, "change": change}

            elif symbol == "NSE:BANKNIFTY":
                data["banknifty"] = {"price": price, "change": change}

            elif symbol == "NSE:FINNIFTY":
                data["finnifty"] = {"price": price, "change": change}

            elif symbol == "NSE:INDIAVIX":
                data["indiavix"] = {"price": price, "change": change}

        # ✅ SAFE FALLBACKS (VERY IMPORTANT)
        for key in ["nifty", "banknifty", "finnifty", "indiavix"]:
            if key not in data:
                data[key] = {"price": 0, "change": 0}

        return data

    except Exception as e:
        print("India Market Error:", str(e))

        # ✅ FULL FALLBACK (prevents crashes in scoring)
        return {
            "nifty": {"price": 0, "change": 0},
            "banknifty": {"price": 0, "change": 0},
            "finnifty": {"price": 0, "change": 0},
            "indiavix": {"price": 0, "change": 0}
        }


def fetch_gift_nifty():
    try:
        payload = {
            "symbols": {
                "tickers": ["SGX:NIFTY1!"],  # proxy
                "query": {"types": []}
            },
            "columns": ["close", "change"]
        }

        res = requests.post(URL, json=payload, headers=HEADERS, timeout=10)
        data_json = res.json()

        items = data_json.get("data", [])

        if not items:
            return {
                "gift_nifty": {"price": 0, "change": 0}
            }

        item = items[0]
        values = item.get("d", [])

        if len(values) < 2:
            return {
                "gift_nifty": {"price": 0, "change": 0}
            }

        return {
            "gift_nifty": {
                "price": values[0],
                "change": values[1]
            }
        }

    except Exception as e:
        print("GIFT Nifty Error:", str(e))

        return {
            "gift_nifty": {"price": 0, "change": 0}
        }