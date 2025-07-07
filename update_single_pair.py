# E:\CODE\FOREX_V2\forex_system\update_single_pair.py

import sys
import os
from pathlib import Path
from forex_system.fetch.fetch_all_data import fetch_data_for_pair
from forex_system.merge_data import consolidate_csv_data
from forex_system.trainer import train_model_for_pair
from forex_system.config import BASE_DIR

def update_single_pair(pair):
    print(f"🔄 Avvio aggiornamento per la coppia: {pair}")

    # Step 1: Fetch dei dati
    print("📥 Recupero dati...")
    try:
        fetch_data_for_pair(pair)
    except Exception as e:
        print(f"❌ Errore durante il fetch dei dati per {pair}: {e}")
        return

    # Step 2: Merge dei dati
    print("🔗 Merge dei dati...")
    try:
        consolidate_csv_data(pair)
    except Exception as e:
        print(f"❌ Errore durante il merge dei dati per {pair}: {e}")
        return
    
    # Step 3: Training del modello
    print("🧠 Addestramento modello...")
    try:
        import pandas as pd
        indicators_path = os.path.join(BASE_DIR, "data", f"indicators_{pair}.csv")
        indicators_df = pd.read_csv(indicators_path)
        train_model_for_pair(pair, indicators_df)
    except Exception as e:
        print(f"❌ Errore durante l'addestramento del modello per {pair}: {e}")
        return


    # Step 3: Training del modello
    print("🧠 Addestramento modello...")
def train_model_for_pair(pair, indicators_df):
    from forex_system.fetch.alpha import AlphaFetcher
    from forex_system.fetch.currencylayer import CurrencyLayerFetcher
    from forex_system.fetch.exchangerates import ExchangeRatesFetcher
    from forex_system.fetch.polygon import PolygonFetcher
    from forex_system.fetch.twelvedata import TwelveDataFetcher
    from forex_system.fetch.yfinance_fetcher import YFinanceFetcher
    from forex_system.fetch.TRADERMADE import TraderMadeFetcher

    fetchers = {
        "Yahoo Finance": YFinanceFetcher(),
        "Alpha Vantage": AlphaFetcher(),
        "TraderMade": TraderMadeFetcher(),
        "CurrencyLayer": CurrencyLayerFetcher(),
        "ExchangeRates": ExchangeRatesFetcher(),
        "Polygon": PolygonFetcher(),
        "TwelveData": TwelveDataFetcher()
    }

    for name, fetcher in fetchers.items():
        try:
            print(f"📡 {name}...")
            fetcher.fetch(pair)
        except Exception as e:
            print(f"⚠️  Errore {name} per {pair}: {e}")

    print(f"✅ Fetch singoli completati per {pair}.")

    # Verifica se i file del modello sono stati creati
    model_files = [
        f"model/model_{pair}.pkl",
        f"model/columns_{pair}.pkl",
        f"model/encoders_{pair}.pkl",
        f"model/scaler_{pair}.pkl"
    ]

    missing = [f for f in model_files if not os.path.exists(f)]
    if missing:
        print(f"❌ Modello NON creato correttamente. Mancano i file: {', '.join(missing)}")
    else:
        print(f"✅ Modello creato correttamente per {pair}: tutti i file .pkl presenti.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("⚠️  Specificare la coppia da aggiornare. Esempio: python update_single_pair.py AUDUSD")
        sys.exit(1)

    forex_pair = sys.argv[1].upper()
    update_single_pair(forex_pair)
 
