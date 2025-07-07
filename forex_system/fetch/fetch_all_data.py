import yfinance as yf
import os
import json
from datetime import datetime, timezone
import pandas as pd
from forex_system.fetch.alpha import AlphaFetcher
from forex_system.fetch.currencylayer import CurrencyLayerFetcher
from forex_system.fetch.exchangerates import ExchangeRatesFetcher
from forex_system.fetch.polygon import PolygonFetcher
from forex_system.fetch.TRADERMADE import TraderMadeFetcher
from forex_system.fetch.twelvedata import TwelveDataFetcher
from forex_system.fetch.yfinance_fetcher import YFinanceFetcher

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")


FETCHERS = {
    "TwelveData": TwelveDataFetcher(),
    "YahooFinance": YFinanceFetcher(),
    "Polygon": PolygonFetcher(),
    "AlphaVantage": AlphaFetcher(),
    "CurrencyLayer": CurrencyLayerFetcher(),
    "ExchangeRates": ExchangeRatesFetcher(),
    "TraderMade": TraderMadeFetcher(),

}

API_USAGE_PATH = os.path.join("srv", "api_usage.json")

def log_api_usage(fetcher_name):
    if not os.path.exists(API_USAGE_PATH):
        usage = {}
    else:
        with open(API_USAGE_PATH, 'r') as file:
            usage = json.load(file)

    today = datetime.now().strftime("%Y-%m-%d")
    usage.setdefault(today, {}).setdefault(fetcher_name, 0)
    usage[today][fetcher_name] += 1

    with open(API_USAGE_PATH, 'w') as file:
        json.dump(usage, file, indent=4)

def check_api_limit(fetcher_name):
    with open(API_USAGE_PATH, 'r') as file:
        usage = json.load(file)

    today = datetime.now().strftime("%Y-%m-%d")
    calls_today = usage.get(today, {}).get(fetcher_name, 0)

    limits = {
        "AlphaVantage": 25,
        "TraderMade": 1000,
        # Aggiungere limiti noti per gli altri fetcher
    }

    limit = limits.get(fetcher_name, float('inf'))
    return calls_today < limit

def is_data_fresh(pair, max_age_minutes=1):
    """
    Controlla se i dati per la coppia Forex sono aggiornati.
    :param pair: La coppia Forex (es. "EURUSD").
    :param max_age_minutes: L'intervallo massimo di freschezza in minuti.
    :return: True se i dati sono aggiornati, False altrimenti.
    """
    csv_path = os.path.join("data", f"market_data_consolidated_{pair}.csv")
    if not os.path.exists(csv_path):
        return False  # Nessun file CSV, i dati non sono aggiornati

    df = pd.read_csv(csv_path)
    if df.empty:
        return False  # Il file CSV è vuoto, i dati non sono aggiornati

    # Controlla il timestamp più recente
    last_timestamp = pd.to_datetime(df["timestamp"].iloc[-1], utc=True)  # Assicura che sia tz-aware
    now = datetime.now(timezone.utc)  # Assicura che il confronto sia tz-aware
    age_minutes = (now - last_timestamp).total_seconds() / 60
    return age_minutes <= max_age_minutes

def fetch_data_for_pair(pair, mode="live"):
    """Fetch dei dati con modalità live o historical"""
    if mode == "live":
        try:
            print(f" Recupero dati live per {pair}...")
            ticker = yf.Ticker(f"{pair}=X")
            # Usa periodo più breve e intervallo più piccolo per dati real-time
            # data = ticker.history(period="1d", interval="1m")
            data = ticker.history(period="30d", interval="1h")  # intervallo 1 ora per storicità
            
            if not data.empty:
                # Verifica latenza
                latest = data.index[-1]
                now = datetime.now(timezone.utc)
                latency = (now - latest.tz_convert(timezone.utc)).total_seconds() / 60
                
                if latency < 5:  # Massimo 5 minuti di latenza
                    df = data.reset_index()
                    df = df.rename(columns={
                        'Datetime': 'timestamp',
                        'Open': 'open',
                        'High': 'high',
                        'Low': 'low',
                        'Close': 'close',
                        'Volume': 'volume'
                    })
                    
                    output_file = os.path.join(DATA_DIR, f"market_data_LIVE_{pair}.csv")
                    # Se esiste già un file consolidato, appende i nuovi dati e rimuove duplicati
                    if os.path.exists(output_file):
                        old_df = pd.read_csv(output_file)
                        combined_df = pd.concat([old_df, df], ignore_index=True)
                        combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], errors='coerce', utc=True)
                        combined_df = combined_df.drop_duplicates(subset='timestamp').sort_values(by='timestamp')
                        combined_df.to_csv(output_file, index=False)
                        print(f" Dati accodati a quelli esistenti per {pair}")
                    else:
                        df.to_csv(output_file, index=False)
                        print(f" Primo salvataggio per {pair}")
                    print(f" Dati real-time aggiornati per {pair} (latenza: {latency:.1f} min)")
                    return True
                else:
                    print(f" Latenza troppo alta: {latency:.1f} min - Provo altri fetcher")
                    
        except Exception as e:
            print(f" Errore nel fetching live: {e}")
            
    # Se il live fetch fallisce o la latenza è troppo alta, prova gli altri fetcher
    for fetcher_name, fetcher in FETCHERS.items():
        if check_api_limit(fetcher_name):
            try:
                data = fetcher.fetch(pair)
                if data is not None and len(data) > 0:
                    fetcher.save_csv(pair, data)
                    log_api_usage(fetcher_name)
                    print(f" Dati recuperati da {fetcher_name}")
                    return True
            except Exception as e:
                print(f" {fetcher_name} fallito: {e}")
                continue
    
    return False

if __name__ == "__main__":
    fetch_data_for_pair("EURUSD")

