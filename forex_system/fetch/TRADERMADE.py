import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Carica la chiave API da .env
from pathlib import Path
load_dotenv(dotenv_path=Path("E:/CODE/FOREX_V2/srv/.env"))
API_KEY = os.getenv("TRADERMADE_API_KEY")
if not API_KEY:
    raise ValueError("⚠️ TRADERMADE_API_KEY non trovata. Controlla il file .env")

import json

LOG_PATH = Path("log/tradermade_requests.json")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def can_make_request(pair):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    try:
        if LOG_PATH.exists():
            with open(LOG_PATH, "r") as f:
                log_data = json.load(f)
        else:
            log_data = {}
    except Exception:
        log_data = {}

    log_data.setdefault(today, [])
    if len(log_data[today]) >= 35:  # max 1000/mese
        print(f" TraderMade: limite giornaliero raggiunto ({len(log_data[today])} richieste oggi)")
        return False, log_data

    return True, log_data

def fetch_tradermade(pair):
    can_fetch, log_data = can_make_request(pair)
    if not can_fetch:
        return None

    url = "https://marketdata.tradermade.com/api/v1/live"
    params = {
        "currency": pair.replace("/", ""),
        "api_key": API_KEY
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code != 200 or "quotes" not in data:
            print(" Errore nella risposta TraderMade:", data)
            return None

        quote = data["quotes"][0]
        timestamp = datetime.utcfromtimestamp(data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")

        df = pd.DataFrame([{
            "timestamp": timestamp,
            "open": quote["mid"],  # TraderMade non fornisce open, low, high
            "high": quote["mid"],
            "low": quote["mid"],
            "close": quote["mid"]
        }])

        symbol = pair.replace("/", "")
        filename = os.path.join("data", f"market_data_{symbol}_tradermade.csv")
        if os.path.exists(filename):
            existing = pd.read_csv(filename)
            df = pd.concat([existing, df], ignore_index=True).drop_duplicates(subset="timestamp")
        df.to_csv(filename, index=False)

        # ✅ Logga la richiesta
        today = datetime.utcnow().strftime("%Y-%m-%d")
        log_data[today].append({
            "timestamp": datetime.utcnow().isoformat(),
            "pair": pair.replace("/", "")
        })
        with open(LOG_PATH, "w") as f:
            json.dump(log_data, f, indent=2)
        print(f" Totale richieste TraderMade oggi: {len(log_data[today])}")

        return df

    except Exception as e:
        print(" Errore durante il fetch:", e)
        return None

def can_use_tradermade():
    from forex_system.config import SRV_PATH
    import os
    import json

    file_path = os.path.join(SRV_PATH, "tradermade_usage.json")
    if not os.path.exists(file_path):
        return True

    with open(file_path, "r") as f:
        data = json.load(f)

    from datetime import datetime
    today = datetime.utcnow().date().isoformat()
    used = data.get(today, 0)

    return used < 35  # max richieste giornaliere

def increment_tradermade_usage():
    from forex_system.config import SRV_PATH
    import os
    import json

    file_path = os.path.join(SRV_PATH, "tradermade_usage.json")
    from datetime import datetime
    today = datetime.utcnow().date().isoformat()

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data[today] = data.get(today, 0) + 1

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

class TraderMadeFetcher:
    def fetch(self, pair):
        df = fetch_tradermade(pair.replace("/", ""))
        if df is not None:
            return df.to_dict(orient="records")
        return []

    def save_csv(self, pair, data):
        if not data:
            return
        df = pd.DataFrame(data)
        os.makedirs("data", exist_ok=True)
        filename = f"data/market_data_TRADERMADE_{pair}.csv"
        df.to_csv(filename, index=False)
        print(f" Salvato CSV TraderMade: {filename}")

# Esempio di test manuale:
if __name__ == "__main__":
    fetch_tradermade("EUR/USD")
 
