import requests
import os
from forex_system.config import EXCHANGERATES_API_KEY
from datetime import datetime

EXCHANGERATES_URL = "https://api.exchangeratesapi.io/v1/latest"

def fetch_exchangerates(pair="EUR/USD"):
    """Recupera i dati di cambio da Exchangeratesapi.io"""
    
    if not EXCHANGERATES_API_KEY:
        print(" Errore: API Key di Exchangeratesapi.io non trovata!")
        return []

    base_currency, quote_currency = pair.split("/")
    
    params = {
        "access_key": EXCHANGERATES_API_KEY,
        "base": base_currency,
        "symbols": quote_currency
    }

    response = requests.get(EXCHANGERATES_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        if "rates" in data:
            return [{
                "timestamp": datetime.utcnow().isoformat(),  # ✅ Generiamo un timestamp valido
                "open": data["rates"][quote_currency],
                "high": data["rates"][quote_currency],
                "low": data["rates"][quote_currency],
                "close": data["rates"][quote_currency],
                "volume": 0
            }]
        else:
            print(f" Errore API Exchangerates: {data}")
            return []
    else:
        print(f" Errore nella richiesta Exchangerates: {response.text}")
        return []

import pandas as pd

class ExchangeRatesFetcher:
    def fetch(self, pair):
        pair_formatted = f"{pair[:3]}/{pair[3:]}"
        return fetch_exchangerates(pair_formatted)

    def save_csv(self, pair, data):
        if not data:
            return
        df = pd.DataFrame(data)
        os.makedirs("data", exist_ok=True)
        filename = f"data/market_data_EXCHANGERATES_{pair}.csv"
        df.to_csv(filename, index=False)
        print(f" Salvato CSV ExchangeRates: {filename}")
