import pandas as pd
import yfinance as yf
from forex_system.fetch.twelvedata import TwelveDataFetcher
from forex_system.fetch.TRADERMADE import TraderMadeFetcher
from forex_system.fetch.polygon import PolygonFetcher
from forex_system.fetch.alpha import AlphaFetcher
import time

# Definisci le coppie da testare
pair_list = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCHF"]

# Elenco dei fetcher
fetchers = {
    "YahooFinance": lambda pair: yf.Ticker(f"{pair}=X").history(period="1d", interval="1m"),
    "TwelveData": TwelveDataFetcher().fetch,
    "TraderMade": TraderMadeFetcher().fetch,
    "Polygon": PolygonFetcher().fetch,
    "AlphaVantage": AlphaFetcher().fetch
}

def test_fetcher(fetcher_name, fetch_func, pair):
    try:
        print(f"🔄 Testando {fetcher_name} per la coppia {pair}...")
        data = fetch_func(pair)
        if isinstance(data, pd.DataFrame) and not data.empty:
            print(f"✅ {fetcher_name} ha risposto correttamente per {pair}")
            return True
        elif isinstance(data, float):
            print(f"✅ {fetcher_name} ha risposto con valore: {data}")
            return True
        else:
            print(f"❌ {fetcher_name} non ha restituito dati validi per {pair}")
            return False
    except Exception as e:
        print(f"⚠️ {fetcher_name} fallito per {pair}: {e}")
        return False

def main():
    print("🚀 Inizio test dei fetcher")
    results = {}

    for pair in pair_list:
        results[pair] = {}
        for fetcher_name, fetch_func in fetchers.items():
            time.sleep(1)  # Pausa per evitare rate limit
            result = test_fetcher(fetcher_name, fetch_func, pair)
            results[pair][fetcher_name] = result
    
    print("\n📊 Risultati del Test:")
    for pair, fetcher_results in results.items():
        print(f"\nCoppia {pair}:")
        for fetcher_name, status in fetcher_results.items():
            status_text = "Successo" if status else "Fallito"
            print(f" - {fetcher_name}: {status_text}")

if __name__ == "__main__":
    main()
