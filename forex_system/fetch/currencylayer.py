import requests
import os
from forex_system.config import CURRENCYLAYER_API_KEY
from datetime import datetime

CURRENCYLAYER_URL = "https://api.currencylayer.com/live"

def fetch_currencylayer(pair="EUR/USD"):
    """Recupera i dati di cambio da Currency Layer"""

    if not CURRENCYLAYER_API_KEY:
        print(" Errore: API Key di Currency Layer non trovata!")
        return []

    base_currency, quote_currency = pair.split("/")

    params = {
        "access_key": CURRENCYLAYER_API_KEY,
        "currencies": quote_currency,
        "source": base_currency,
        "format": 1
    }

    response = requests.get(CURRENCYLAYER_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        if "quotes" in data:
            rate_key = f"{base_currency}{quote_currency}"
            return [{
                "timestamp": datetime.utcnow().isoformat(),  # ✅ Generiamo un timestamp valido
                "open": data["quotes"].get(rate_key, "N/A"),
                "high": data["quotes"].get(rate_key, "N/A"),
                "low": data["quotes"].get(rate_key, "N/A"),
                "close": data["quotes"].get(rate_key, "N/A"),
                "volume": 0
            }]
        else:
            print(f" Errore API Currency Layer: {data}")
            return []
    else:
        print(f" Errore nella richiesta Currency Layer: {response.text}")
        return []

import pandas as pd

class CurrencyLayerFetcher:
    def fetch(self, pair):
        pair_formatted = f"{pair[:3]}/{pair[3:]}"
        return fetch_currencylayer(pair_formatted)

    def save_csv(self, pair, data):
        if not data:
            return
        df = pd.DataFrame(data)
        os.makedirs("data", exist_ok=True)
        filename = f"data/market_data_CURRENCYLAYER_{pair}.csv"
        df.to_csv(filename, index=False)
        print(f" Salvato CSV CurrencyLayer: {filename}")
