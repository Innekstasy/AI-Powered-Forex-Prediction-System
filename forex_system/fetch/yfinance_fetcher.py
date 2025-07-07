import yfinance as yf
import pandas as pd
import os

def fetch_yahoo_forex(pair="EUR/USD"):
    """ Recupera dati Forex da Yahoo Finance """
    forex_pair = pair.replace("/", "") + "=X"  # Yahoo usa EURUSD=X
    df = yf.download(forex_pair, period="30d", interval="1d", auto_adjust=False)  # Scarichiamo 30 giorni di dati

    if df.empty:
        raise Exception(f"Nessun dato trovato per {pair} su Yahoo Finance.")

    df["timestamp"] = df.index
    df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)
    df["volume"] = 0  # Yahoo non fornisce volume per Forex
    return df[["timestamp", "open", "high", "low", "close", "volume"]].to_dict(orient="records")

if __name__ == "__main__":
    test_data = fetch_yahoo_forex()
    print(test_data)

class YFinanceFetcher:
    def fetch(self, pair):
        return fetch_yahoo_forex(pair)

    def save_csv(self, pair, data):
        if not data:
            return
        df = pd.DataFrame(data)
        os.makedirs("data", exist_ok=True)
        filename = f"data/market_data_YFINANCE_{pair}.csv"
        df.to_csv(filename, index=False)
        print(f" Salvato CSV Yahoo Finance: {filename}")
