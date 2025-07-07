 
import requests
import os
import json
from forex_system.config import TWELVEDATA_API_KEY, TWELVEDATA_URL


def fetch_twelvedata(pair="EUR/USD", interval="1day"):
    """ Recupera dati dal TwelveData API con il formato corretto """
    params = {
        "symbol": pair,  # Usa EUR/USD invece di EURUSD
        "interval": interval,
        "apikey": TWELVEDATA_API_KEY
    }

    response = requests.get(TWELVEDATA_URL + "/time_series", params=params)

    if response.status_code == 200:
        data = response.json()
        if "values" in data:
            result = []
            for d in data["values"]:
                result.append({
                    "timestamp": d["datetime"],
                    "open": float(d["open"]),
                    "high": float(d["high"]),
                    "low": float(d["low"]),
                    "close": float(d["close"]),
                    "volume": 0
                })
            return result
        else:
            raise Exception(f"Errore API: {data}")
    else:
        raise Exception(f"Errore nella richiesta: {response.text}")

import pandas as pd

class TwelveDataFetcher:
    def fetch(self, pair):
        # TwelveData richiede il formato EUR/USD
        pair_formatted = f"{pair[:3]}/{pair[3:]}"
        return fetch_twelvedata(pair_formatted)

    def save_csv(self, pair, data):
        if not data:
            return
        df = pd.DataFrame(data)
        os.makedirs("data", exist_ok=True)
        filename = f"data/market_data_TWELVEDATA_{pair}.csv"
        df.to_csv(filename, index=False)
        print(f" Salvato CSV TwelveData: {filename}")

if __name__ == "__main__":
    test_data = fetch_twelvedata()
    print(test_data)
