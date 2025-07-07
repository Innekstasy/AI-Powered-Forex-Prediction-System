import requests
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from forex_system.config import POLYGON_API_KEY, POLYGON_URL
from forex_system.config import SRV_PATH


USAGE_FILE = os.path.join(SRV_PATH, "polygon_usage.json")
MAX_REQUESTS = 500  # Polygon.io ha limiti più alti di Alpha Vantage

def check_api_usage():
    """ Legge il file di utilizzo API e aggiorna il conteggio se è un nuovo giorno """
    if not os.path.exists(USAGE_FILE):
        return {"date": datetime.today().strftime('%Y-%m-%d'), "count": 0}

    with open(USAGE_FILE, "r") as f:
        data = json.load(f)

    today = datetime.today().strftime('%Y-%m-%d')

    # Reset del conteggio se è un nuovo giorno
    if data["date"] != today:
        data = {"date": today, "count": 0}
    
    return data

def update_api_usage(count):
    """ Aggiorna il conteggio delle richieste nel file JSON """
    usage_data = {"date": datetime.today().strftime('%Y-%m-%d'), "count": count}
    
    with open(USAGE_FILE, "w") as f:
        json.dump(usage_data, f)

def fetch_polygon_data(pair="EUR/USD"):
    forex_pair = pair.replace("/", "")
    url = f"{POLYGON_URL}/v1/last_quote/currencies/{forex_pair[:3]}/{forex_pair[3:]}"
    headers = {"Authorization": f"Bearer {POLYGON_API_KEY}"}
    
    print(f"URL generato: {url}")  # Debug URL

    try:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f" Errore Polygon ({response.status_code}): {response.text}")
            return []

        data = response.json()
        if "last" not in data:
            print(" Polygon: 'last' non presente nella risposta.")
            return []

        result = [{
            "timestamp": datetime.utcnow().isoformat(),
            "open": data["last"]["ask"],
            "high": data["last"]["ask"],
            "low": data["last"]["bid"],
            "close": data["last"]["bid"],
            "volume": 0  # I dati tick-by-tick potrebbero non includere il volume
        }]
        print(f" Polygon: dati ricevuti per {pair}")
        return result

    except Exception as e:
        print(f" Errore durante richiesta Polygon: {e}")
        return []

class PolygonFetcher:
    def fetch(self, pair):
        return fetch_polygon_data(pair.replace("/", ""))

    def save_csv(self, pair, data):
        if not data:
            return
        df = pd.DataFrame(data)
        filename = f"data/market_data_POLYGON_{pair}.csv"
        df.to_csv(filename, index=False)
        print(f" Salvato CSV Polygon: {filename}")

if __name__ == "__main__":
    test_data = fetch_polygon_data()
    print(test_data)


