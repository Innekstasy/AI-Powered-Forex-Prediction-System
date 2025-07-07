import os
import pandas as pd
from datetime import datetime, timedelta

# === CONFIGURAZIONE ===
DAYS_THRESHOLD = 15
PREDICTION_DIR = r"E:\CODE\FOREX_V3\log\predictions"

def is_old_signal(row, threshold_date):
    try:
        ts = pd.to_datetime(row['timestamp'], errors='coerce')
        return pd.notna(ts) and ts < threshold_date
    except Exception:
        return False

def clean_pending_signals():
    print(f" Avvio pulizia segnali IN ATTESA più vecchi di {DAYS_THRESHOLD} giorni...")

    now = datetime.utcnow()
    threshold_date = now - timedelta(days=DAYS_THRESHOLD)
    removed_total = 0
    files_processed = 0

    for file in os.listdir(PREDICTION_DIR):
        if file.startswith("market_prediction_") and file.endswith(".csv"):
            file_path = os.path.join(PREDICTION_DIR, file)
            try:
                df = pd.read_csv(file_path)
                print(f"\n {file}")
                if 'status' in df.columns:
                    print(" status unique:", df['status'].dropna().unique())
                if 'timestamp' in df.columns:
                    print(" timestamp min:", df['timestamp'].min())
                    print(" timestamp max:", df['timestamp'].max())
                    if not df['timestamp'].dropna().empty:
                        print(" esempio:", df['timestamp'].dropna().iloc[0])
                    else:
                        print("  Nessun timestamp valido presente.")
                else:
                    print("  timestamp non trovato.")

                if 'status' not in df.columns or 'timestamp' not in df.columns:
                    continue

                original_len = len(df)
                df = df[~df.apply(lambda row: is_old_signal(row, threshold_date), axis=1)]
                new_len = len(df)
                removed = original_len - new_len

                if removed > 0:
                    df.to_csv(file_path, index=False)
                    print(f"  {file}: rimossi {removed} segnali vecchi")
                    removed_total += removed
                files_processed += 1

            except Exception as e:
                print(f" Errore su {file}: {e}")

    print(f"\n Pulizia completata: {files_processed} file processati, {removed_total} segnali rimossi.")

if __name__ == "__main__":
    clean_pending_signals()
 
