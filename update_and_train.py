import os, sys
import time
import json
import pandas as pd
import glob
import threading
from forex_system.fetch.fetch_all_data import fetch_data_for_pair
from forex_system.merge_data import consolidate_csv_data
from forex_system.indicators.loader import calculate_all_indicators
from forex_system.trainer import train_model_for_pair
from forex_system.indicators.ml import calculate_ml_indicator

from datetime import datetime, timezone
from datetime import timedelta
import traceback

from forex_system.config import LOG_PATH, DATA_PATH, SRV_PATH

TRAINING_INFO_FILE = os.path.join(SRV_PATH, "training_info.json")

# def listen_for_restart():
#     while True:
#         cmd = input(">>> Digita 'r' e premi Invio per riavviare lo script: ").strip().lower()
#         if cmd == 'r':
#             print("🔁 Riavvio in corso...")
#             python = sys.executable
#             os.execl(python, python, *sys.argv)

# Avvia il listener in un thread separato
# threading.Thread(target=listen_for_restart, daemon=True).start()

def load_training_info():
    if os.path.exists(TRAINING_INFO_FILE):
        with open(TRAINING_INFO_FILE, "r") as f:
            return json.load(f)
    return {}

def save_training_info(data):
    with open(TRAINING_INFO_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_custom_pair(pair):
    """Salva le coppie personalizzate in un file separato."""
    custom_pairs_path = os.path.join(SRV_PATH, "custom_pairs.json")
    custom_pairs = []
    if os.path.exists(custom_pairs_path):
        with open(custom_pairs_path, 'r') as f:
            custom_pairs = json.load(f)

    if pair not in custom_pairs:
        custom_pairs.append(pair)
        with open(custom_pairs_path, 'w') as f:
            json.dump(custom_pairs, f, indent=4)
        print(f" Coppia personalizzata salvata: {pair}")

def is_pending_expired(timestamp, max_hours=24):
    """Controlla se il segnale pending è scaduto"""
    try:
        trade_time = pd.to_datetime(timestamp, utc=True)
        time_diff = datetime.now(timezone.utc) - trade_time
        return time_diff > timedelta(hours=max_hours)
    except Exception as e:
        print(f" Errore nel controllo scadenza pending: {e}")
        return False

def log(msg: str):
    timestamp = datetime.utcnow().isoformat()
    line = f"[{timestamp}] {msg}"
    print(line)  # Stampa diretta per debug
    with open(os.path.join(LOG_PATH, "update_and_train.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")

# Configurazione
PAIR_OPTIONS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "USDCHF",
    "AUDUSD"
]
CONFIG_PATH = os.path.join('srv', 'last_selected_pair.json')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CHECK_INTERVAL = 1 * 60 * 60  # 1 ore in secondi

def load_custom_pairs():
    """Carica tutte le coppie personalizzate registrate."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
            custom_pair = config.get("last_selected_pair")
            if custom_pair:
                if custom_pair not in PAIR_OPTIONS:
                    PAIR_OPTIONS.append(custom_pair)
                    print(f" Aggiunta nuova coppia personalizzata: {custom_pair}")

    # Rileggi tutte le coppie dal file di log delle coppie personalizzate
    custom_pairs_path = os.path.join(SRV_PATH, "custom_pairs.json")
    if os.path.exists(custom_pairs_path):
        with open(custom_pairs_path, 'r') as f:
            custom_pairs = json.load(f)
            for pair in custom_pairs:
                if pair not in PAIR_OPTIONS:
                    PAIR_OPTIONS.append(pair)
                    print(f" Aggiunta coppia personalizzata da file: {pair}")

def fetch_data_for_pair(pair):
    """Migliora il fetching dei dati con gestione latenza"""
    print(f" Fetching dati per {pair}...")
    success = False
    
    # Import yfinance
    import yfinance as yf
    
    try:
        ticker = yf.Ticker(f"{pair}=X")
        # Usa intervallo di 1 minuto per dati più freschi
        data = ticker.history(period="1y", interval="1h")
        
        if not data.empty and len(data) > 100:
            # Verifica latenza
            latest = data.index[-1]
            now = datetime.now(timezone.utc)
            latency = (now - latest.tz_convert(timezone.utc)).total_seconds() / 60
            
            if latency < 5:  # Massimo 5 minuti di latenza per dati live
                success = True
                # Salva direttamente come consolidated per evitare il merge
                df = data.reset_index()
                df = df.rename(columns={
                    'Datetime': 'timestamp',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                })
                output_file = os.path.join(DATA_PATH, f"market_data_consolidated_{pair}.csv")

                if os.path.exists(output_file):
                    df_existing = pd.read_csv(output_file)
                    df_existing['timestamp'] = pd.to_datetime(df_existing['timestamp'], errors='coerce', utc=True)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)

                    # Elimina righe con timestamp nulli o colonne critiche NaN
                    df_existing = df_existing.dropna(subset=["timestamp", "open", "high", "low", "close"])
                    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"])

                    if not df_existing.empty and not df.empty:
                        df = pd.concat([df_existing, df], ignore_index=True)
                    else:
                        df = df_existing if not df_existing.empty else df

                    df = df.drop_duplicates(subset='timestamp').sort_values(by='timestamp')

                else:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
                    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"])

                df.to_csv(output_file, index=False)

                print(f" Dati live aggiornati per {pair} (latenza: {latency:.1f} min)")
                return True
            else:
                print(f" Latenza troppo alta: {latency:.1f} min")
    except Exception as e:
        print(f" Errore Yahoo Finance: {str(e)}")

    return success

def has_significant_change(pair):
    """Verifica se ci sono stati cambiamenti significativi nei dati"""
    csv_path = os.path.join(DATA_PATH, f"market_data_consolidated_{pair}.csv")
    if not os.path.exists(csv_path):
        return True

    df = pd.read_csv(csv_path)
    
    if len(df) < 1000:
        print(f" CSV consolidato per {pair} ha meno di 1000 righe ({len(df)})")
        return True

    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        latest = df['timestamp'].max()
        latency = (datetime.now(timezone.utc) - latest).total_seconds() / 3600
        
        if latency > 4:
            print(f" CSV consolidato troppo vecchio per {pair}")
            print(f"   Ultimo aggiornamento: {latest}")
            print(f"   Latenza: {latency:.1f} ore")
            return True
    except Exception as e:
        print(f" Errore nel controllo timestamp: {e}")
        return True

    return False

# def check_csv_updated(pair):
#    csv_path = os.path.join(DATA_DIR, f"market_data_consolidated_{pair}.csv")
#    if not os.path.exists(csv_path):
#        raise ValueError(f"❌ Il file CSV per {pair} non esiste. Esegui update_and_train.py per aggiornare i dati.")
#    last_modified = os.path.getmtime(csv_path)
#    print(f"📅 Ultimo aggiornamento per {pair}: {datetime.fromtimestamp(last_modified)}")

def update_and_train():
    """Esegue il fetching dei dati e aggiorna i modelli in un loop."""

    skipped_pairs = set()  # <= SPOSTATA QUI DENTRO il try, all'inizio del ciclo

    while True:
        try:
            print(" Inizio ciclo di aggiornamento...")  # Debug

            # PATCH: verifica se il mercato Forex è aperto (domenica 22:00 → venerdì 22:00 UTC)
            now_utc = datetime.utcnow()
            day = now_utc.weekday()  # 0 = lunedì, 6 = domenica
            hour = now_utc.hour

            # Mercato chiuso: venerdì >= 22 UTC oppure sabato oppure domenica < 22
            if (day == 4 and hour >= 22) or (day == 5) or (day == 6 and hour < 22):
                print(f" Mercati Forex CHIUSI (UTC {now_utc.strftime('%A %H:%M')}) → attendo apertura...")
                print(f" Attesa di {CHECK_INTERVAL // 3600} ore prima del prossimo controllo...")
                time.sleep(CHECK_INTERVAL)
                continue

            load_custom_pairs()

            for pair in PAIR_OPTIONS:
                if pair in skipped_pairs:
                    print(f"  Salto {pair} (già fallito in questo ciclo).")
                    continue

                print(f" Controllo aggiornamenti per {pair}...")

                try:
                    if has_significant_change(pair):
                        print(f" Fetching dati per {pair}...")
                        fetch_data_for_pair(pair)
                        consolidate_csv_data(pair)

                    print(f" Calcolo indicatori per {pair}...")
                    try:
                        indicators_df = calculate_all_indicators(pair)
                        indicators_df = calculate_ml_indicator(indicators_df, pair, model_dir="model")
                    except ValueError as ve:
                        print(f" Errore con {pair}: {ve}")
                        skipped_pairs.add(pair)
                        continue

                    if not indicators_df.empty and len(indicators_df) >= 10:
                        print(f" Pulizia dati da NaN e valori infiniti per {pair}...")
                        indicators_df = indicators_df.replace([float("inf"), float("-inf")], pd.NA)
                        threshold = 0.8 * indicators_df.shape[1]
                        # indicators_df = indicators_df.dropna(thresh=threshold)

                        core_cols = ["RSI_score", "SMA_score", "Fibonacci_score", "support_resistance_score", "wyckoff_score"]
                        optional_cols = ["ML_CONFIDENCE_SCORE", "ML_MARKET_BIAS_SCORE"]
                        cols_to_check = [col for col in core_cols if col in indicators_df.columns]
                        indicators_df = indicators_df.dropna(subset=cols_to_check)


                        # (Opzionale ma utile) Clipping dei valori troppo grandi
                        indicators_df = indicators_df.apply(pd.to_numeric, errors='coerce')
                        indicators_df = indicators_df.clip(lower=-1e6, upper=1e6)

                        if indicators_df.empty:
                            print(f" Dati puliti insufficienti per addestrare il modello per {pair}.")
                            skipped_pairs.add(pair)
                            continue

                        print(f" Addestramento modello per {pair}...")
                        train_model_for_pair(pair, indicators_df)

                        # Aggiorna training_info.json
                        training_info = load_training_info()
                        training_info[pair] = datetime.utcnow().isoformat()
                        training_info[f"{pair}_rows"] = len(indicators_df)
                        save_training_info(training_info)
                    
                        if pair in skipped_pairs:
                            print(f" Dati insufficienti o errore per {pair}. Skipping.")
                        else:
                            print(f" Ciclo completato per {pair}.")

                except Exception as pair_exception:
                    print(f" Errore durante il processing di {pair}: {pair_exception}")
                    skipped_pairs.add(pair)
                    continue

            # Verifica dei segnali pending scaduti
            print(" Verifica dei segnali pending scaduti...")
            pending_dir = os.path.join("log", "predictions")
            pending_files = glob.glob(os.path.join(pending_dir, "market_prediction_*.csv"))

            for file in pending_files:

                if os.path.getsize(file) == 0:
                    print(f" File vuoto ignorato: {file}")
                    continue

                try:
                    df = pd.read_csv(file)

                    # Verifica se la colonna 'status' esiste, altrimenti la crea con valore 'IN ATTESA'
                    if 'status' not in df.columns:
                        print(f" Colonna 'status' mancante nel file {file}. Inizializzazione con valore 'IN ATTESA'.")
                        df['status'] = "IN ATTESA"

                    # for index, trade in df.iterrows():
                    #     if trade['status'] == "IN ATTESA" and is_pending_expired(trade['timestamp']):
                    #         print(f"⚠️ Segnale pending scaduto per {trade['pair']} - Chiusura automatica.")
                    #         df.at[index, 'status'] = "SCADUTO"

                    required_cols = {'pair', 'timestamp', 'status'}
                    if not required_cols.issubset(df.columns):
                        print(f" File {file} non contiene tutte le colonne richieste ({required_cols}). Skipping.")
                        continue

                    df['status'] = df['status'].astype(str)

                    for index, trade in df.iterrows():
                        try:
                            if trade['status'] == "IN ATTESA" and is_pending_expired(trade['timestamp']):
                                print(f" Segnale pending scaduto per {trade['pair']} - Chiusura automatica.")
                                df.at[index, 'status'] = "SCADUTO"
                        except Exception as e:
                            print(f" Errore nel parsing riga pending: {e}")

                    # Salva il CSV aggiornato
                    df.to_csv(file, index=False)
                except Exception as e:
                    print(f"Errore nel controllo dei pending: {e}")

            # 📊 RIEPILOGO DEL CICLO
            # Conta quanti modelli sono stati creati, quante coppie sono state fetchate e quanti pending sono stati chiusi

            # Calcolo riepilogo
            try:
                updated_csvs = glob.glob(os.path.join(DATA_PATH, "market_data_consolidated_*.csv"))
                num_updated_pairs = len(updated_csvs)

                model_files = glob.glob(os.path.join("model", "model_*.pkl"))
                num_models = len(model_files)

                # Conta i segnali scaduti
                expired_signals = 0
                for file in glob.glob(os.path.join("log", "predictions", "market_prediction_*.csv")):
                    df = pd.read_csv(file)
                    expired_signals += (df['status'] == 'SCADUTO').sum()

                print(f" Fine ciclo | Dati aggiornati: {num_updated_pairs} coppie | Modelli esistenti: {num_models} | Pending scaduti: {expired_signals}")
            except Exception as summary_err:
                print(f" Errore durante il riepilogo ciclo: {summary_err}")

            # Countdown per il prossimo ciclo
            print(f" Attesa di {CHECK_INTERVAL // 3600} ore prima del prossimo ciclo...")
            for remaining in range(CHECK_INTERVAL, 0, -300):  # Controlla ogni 5 minuti (300 secondi)
                print(f" Tempo rimanente: {remaining // 60} minuti... (Controllo CSV in corso)")
                time.sleep(300)  # Aspetta 5 minuti

        except Exception as e:
            print(f" Errore durante l'esecuzione: {e}")
            traceback.print_exc()

print(f" Percorso DATA_PATH: {DATA_PATH}")
print(f" Percorso LOG_PATH: {LOG_PATH}")

if __name__ == "__main__":
    update_and_train()

