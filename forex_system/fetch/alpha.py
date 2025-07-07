import requests
import json
import os
from datetime import datetime
from forex_system.config import ALPHA_VANTAGE_API_KEY, ALPHA_VANTAGE_URL
from forex_system.config import SRV_PATH


API_USAGE_FILE = os.path.join(SRV_PATH, "api_usage.json")

def check_api_limit():
    """Verifica se il limite di richieste giornaliere è stato raggiunto e aggiorna il file se necessario."""
    today = datetime.today().strftime("%Y-%m-%d")

    # Se il file non esiste, inizializza il contatore
    if not os.path.exists(API_USAGE_FILE):
        with open(API_USAGE_FILE, "w") as f:
            json.dump({"date": today, "count": 0}, f)
        return True

    # Legge il file JSON
    with open(API_USAGE_FILE, "r") as f:
        data = json.load(f)

    # Se il giorno è cambiato, resetta il contatore
    if data["date"] != today:
        data = {"date": today, "count": 0}
        with open(API_USAGE_FILE, "w") as f:
            json.dump(data, f)
        return True

    # Se il limite di 25 richieste è stato raggiunto, blocca la richiesta
    if data["count"] >= 25:
        print(" Alpha Vantage: LIMITE DI 25 RICHIESTE RAGGIUNTO. VERRÀ SALTATO.")
        return False

    return True

def update_api_usage():
    """Aggiorna il conteggio delle richieste API."""
    today = datetime.today().strftime("%Y-%m-%d")

    # Legge il file JSON
    with open(API_USAGE_FILE, "r") as f:
        data = json.load(f)

    # Verifica se il giorno è cambiato
    if data["date"] != today:
        data = {"date": today, "count": 1}  # Reset e imposta a 1 per la richiesta corrente
    else:
        data["count"] += 1

    # Salva il conteggio aggiornato
    with open(API_USAGE_FILE, "w") as f:
        json.dump(data, f)

    return data["count"]
def fetch_alpha_vantage(pair="EUR/USD"):
    """Recupera dati giornalieri da Alpha Vantage"""

    # 📌 Controlliamo se la chiave API è presente e valida
    if not ALPHA_VANTAGE_API_KEY or ALPHA_VANTAGE_API_KEY == "YOUR_API_KEY":

        print(" Errore: La chiave API di Alpha Vantage non è impostata correttamente!")
        return []

    # Verifica il limite API prima di fare la richiesta
    if not check_api_limit():
        return []  # 🚫 Se il limite è raggiunto, restituiamo una lista vuota e bypassiamo Alpha Vantage

    # Estrai correttamente le valute dalla coppia
    currencies = pair.split('/')
    if len(currencies) != 2:
        print(f" Formato coppia non valido: {pair}. Usa il formato 'XXX/YYY'.")
        return []

    from_currency = currencies[0]
    to_currency = currencies[1]

    url = f"{ALPHA_VANTAGE_URL}?function=FX_DAILY&from_symbol={from_currency}&to_symbol={to_currency}&apikey={ALPHA_VANTAGE_API_KEY}"
    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if "Time Series FX (Daily)" in data:
                count = update_api_usage()  # ✅ Aggiorna il contatore SOLO se la risposta è valida
                print(f" Alpha Vantage: Richiesta {count}/25 completata con successo per {pair}.")
                result = []
                for k, v in data["Time Series FX (Daily)"].items():
                    result.append({
                        "timestamp": k,
                        "open": float(v["1. open"]),
                        "high": float(v["2. high"]),
                        "low": float(v["3. low"]),
                        "close": float(v["4. close"]),
                        "volume": 0
                    })
                return result
            else:
                print(f" Alpha Vantage ha restituito un errore per {pair}: {data}")
                return []  # 🚫 Non aggiorniamo il contatore in caso di errore
        else:
            print(f" Errore nella richiesta per {pair}: {response.text}")
            return []
    except Exception as e:
        print(f" Errore durante la richiesta Alpha Vantage per {pair}: {str(e)}")
        return []

import pandas as pd

class AlphaFetcher:
    def fetch(self, pair):
        # Conversione per lo standard: EURUSD → EUR/USD
        pair_formatted = f"{pair[:3]}/{pair[3:]}"
        return fetch_alpha_vantage(pair_formatted)

    def save_csv(self, pair, data):
        if not data:
            return
        df = pd.DataFrame(data)

        os.makedirs("data", exist_ok=True)  # 👈 crea la cartella se non esiste

        filename = f"data/market_data_ALPHA_{pair}.csv"
        df.to_csv(filename, index=False)
        print(f" Salvato CSV Alpha Vantage: {filename}")



if __name__ == "__main__":
    test_data = fetch_alpha_vantage()
    print(test_data)
