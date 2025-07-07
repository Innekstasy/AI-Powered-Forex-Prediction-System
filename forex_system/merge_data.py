import pandas as pd
import glob
import os
from datetime import datetime, timedelta, timezone

FETCHERS_ACRONYMS = [
    "ALPHA",
    "CURRENCYLAYER",
    "EXCHANGERATES",
    "POLYGON",
    "TRADERMADE",
    "TWELVEDATA",
    "YFINANCE",
    "LIVE"
]

DATA_DIR = os.path.join("data")
OUTPUT_DIR = DATA_DIR  # Salvato nella stessa cartella dati consolidati

def consolidate_csv_data(pair, priority_live=True):
    """Consolida i dati dando priorità ai dati live"""
    
    # 1. Prima verifica se esistono dati LIVE recenti
    live_file = os.path.join(DATA_DIR, f"market_data_LIVE_{pair}.csv")
    if os.path.exists(live_file):
        df = pd.read_csv(live_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        latest = df['timestamp'].max()
        now = datetime.now(timezone.utc)
        latency = (now - latest).total_seconds() / 60
        
        # Se i dati LIVE sono freschi (< 5 min), usali direttamente
        if latency < 5:
            print(f" Usando dati LIVE freschi per {pair} (latenza: {latency:.1f} min)")
            output_file = os.path.join(OUTPUT_DIR, f"market_data_consolidated_{pair}.csv")
            df.to_csv(output_file, index=False)
            print(f"\n CSV consolidato creato: {output_file}")
            return df  # ⛔ Blocca l'esecuzione prima del merge successivo
            
    # 2. Se non ci sono dati LIVE freschi, procedi con il merge normale
    pattern = os.path.join(DATA_DIR, f"market_data_*_{pair}.csv")
    files = [f for f in glob.glob(pattern) if "CONSOLIDATED" not in os.path.basename(f).upper()]
    
    if not files:
        raise FileNotFoundError(f"Nessun CSV trovato per la coppia {pair}")

    # Separa file live e storici
    live_files = [f for f in files if "LIVE" in f.upper()]
    historical_files = [f for f in files if "LIVE" not in f.upper()]
    
    # Ordina in base alla priorità
    files_to_process = live_files + historical_files if priority_live else historical_files + live_files

    dfs = []
    for file in files_to_process:
        fetcher_acronym = [acronym for acronym in FETCHERS_ACRONYMS if acronym in file.upper()]
        if fetcher_acronym:
            df = pd.read_csv(file)
            
            # Uniforma il formato del timestamp
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
            
            dfs.append(df)
            print(f"Aggiunto CSV dal fetcher: {fetcher_acronym[0]} per {pair}")
        else:
            print(f"File non riconosciuto o non conforme: {file}")

    if not dfs:
        raise ValueError("Nessun dato valido trovato nei file CSV.")

    # Consolidamento dei dati
    dfs = [df for df in dfs if not df.empty and df.dropna(how='all').shape[1] > 0]
    consolidated_df = pd.concat(dfs, ignore_index=True)

    # 🔍 FIX: pulizia dei timestamp corrotti/nulli
    consolidated_df['timestamp'] = pd.to_datetime(consolidated_df['timestamp'], errors='coerce', utc=True)
    consolidated_df = consolidated_df.dropna(subset=['timestamp'])

    # Rimuovi le colonne duplicate da YFinance
    columns_to_drop = [col for col in consolidated_df.columns if isinstance(col, tuple)]
    if any(isinstance(col, tuple) for col in consolidated_df.columns):
        consolidated_df.columns = ['_'.join(filter(None, map(str, col))) for col in consolidated_df.columns]
    consolidated_df = consolidated_df.drop(columns=columns_to_drop)

    # Assicurati che tutte le colonne necessarie siano presenti
    required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    for col in required_columns:
        if col not in consolidated_df.columns:
            print(f" Colonna mancante: {col}, creazione con valori di default")
            consolidated_df[col] = 0

    # Rimuovi i duplicati e ordina
    consolidated_df = consolidated_df.drop_duplicates(subset=['timestamp']).sort_values(by='timestamp')

    # Filtra solo i dati degli ultimi 30 giorni
    # last_30_days = datetime.now(timezone.utc) - timedelta(days=30)
    # consolidated_df['timestamp'] = pd.to_datetime(consolidated_df['timestamp'], utc=True)
    # consolidated_df = consolidated_df[consolidated_df['timestamp'] >= last_30_days]

    # NON FILTRARE più i dati. Manteniamo tutta la storicità.
    consolidated_df['timestamp'] = pd.to_datetime(consolidated_df['timestamp'], utc=True)

    # Riempi i valori mancanti
    price_columns = ['open', 'high', 'low', 'close']
    consolidated_df[price_columns] = consolidated_df[price_columns].ffill().bfill()
    consolidated_df['volume'] = consolidated_df['volume'].fillna(0)

    # Verifica la qualità dei dati
    #print("\n📊 Statistiche dei dati consolidati:")
    #print(f"Righe totali: {len(consolidated_df)}")
    #print("Valori mancanti:")
    #print(consolidated_df.isnull().sum())
    #print("\nRange dei prezzi:")
    for col in price_columns:
        print(f"{col}: {consolidated_df[col].min():.5f} - {consolidated_df[col].max():.5f}")

    # Modifica: Assicuriamoci prima di tutto che i dati LIVE siano recenti
    if priority_live and live_files:
        for file in live_files:
            df = pd.read_csv(file)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
                latest = df['timestamp'].max()
                now = datetime.now(timezone.utc)
                latency = (now - latest).total_seconds() / 60
                
                if latency > 5:  # Se i dati live sono vecchi più di 5 minuti
                    print(f" Dati live troppo vecchi per {pair} (latenza: {latency:.1f} min)")
                    live_files.remove(file)  # Rimuovi il file live dai files da processare

    # Modifica: Aggiungi log della latenza finale
    if not consolidated_df.empty:
        latest = consolidated_df['timestamp'].max()
        now = datetime.now(timezone.utc)
        final_latency = (now - latest).total_seconds() / 60
        print(f" Latenza finale dei dati consolidati: {final_latency:.1f} min")

    output_file = os.path.join(OUTPUT_DIR, f"market_data_consolidated_{pair}.csv")
    consolidated_df.to_csv(output_file, index=False)
    print(f"\n CSV consolidato creato: {output_file}")
    
    return consolidated_df

if __name__ == "__main__":
    consolidate_csv_data("EURUSD")

