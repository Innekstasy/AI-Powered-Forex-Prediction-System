import pandas as pd
import os
import numpy as np
from datetime import datetime, timezone

from .fibonacci import calculate_fibonacci_levels
from .rsi import calculate_rsi
from .sma_atr import calculate_sma_atr
from .support_resistance import calculate_support_resistance
from .wyckoff import calculate_wyckoff_phases
from .ml import calculate_ml_indicator
from colorama import init, Fore, Style
init()  # Abilita il supporto su Windows

DATA_DIR = os.path.join("data")
MODEL_DIR = os.path.join("model")

def validate_data_quality(df):
    """Verifica la qualità dei dati prima del calcolo degli indicatori"""
    # Verifica prezzi negativi o nulli
    price_columns = ['open', 'high', 'low', 'close']
    for col in price_columns:
        if (df[col] <= 0).any():
            print(f" Trovati prezzi non validi in {col}")
            df[col] = df[col].mask(df[col] <= 0, method='ffill')

    # Verifica che high sia sempre >= low
    invalid_hl = df['high'] < df['low']
    if invalid_hl.any():
        print(" Trovati high/low non validi, correzione in corso...")
        df.loc[invalid_hl, ['high', 'low']] = df.loc[invalid_hl, ['low', 'high']].values

    # Rimuovi le colonne duplicate da YFinance
    duplicate_cols = [col for col in df.columns if isinstance(col, tuple)]
    if duplicate_cols:
        print(" Rimozione colonne duplicate da YFinance...")
        df = df.drop(columns=duplicate_cols)

    # Converti e pulisci i valori numerici
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_columns:
        if col in price_columns:
            df[col] = df[col].ffill().bfill()  # Updated deprecated method
        else:
            df[col] = df[col].fillna(df[col].mean()).fillna(0)

    # Verifica che non ci siano infiniti o NaN
    if df.isin([np.inf, -np.inf]).any().any():
        print(" Trovati valori infiniti, sostituzione con NaN...")
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(method='ffill').fillna(method='bfill')

    return df

def check_data_freshness(df, max_latency_minutes=5):
    """Verifica la freschezza dei dati"""
    now = datetime.now(timezone.utc)
    last_timestamp = pd.to_datetime(df["timestamp"].iloc[-1], utc=True)
    latency = (now - last_timestamp).total_seconds() / 60

    if latency > max_latency_minutes:
        print(f"\n ATTENZIONE: Latenza elevata ({latency:.1f} min)")
        print(f"Ultimo aggiornamento: {last_timestamp}")
        return False
    
    print(f"\n Dati aggiornati (latenza: {latency:.1f} min)")
    return True

def calculate_all_indicators(pair):
    input_csv = os.path.join(DATA_DIR, f"market_data_consolidated_{pair}.csv")
    df = pd.read_csv(input_csv)

    #print("📊 Colonne nel CSV:", df.columns.tolist())
    #print("📈 Numero righe nel CSV:", len(df))
    #print(df.head(3))  # Mostra le prime 3 righe per il debug

    required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f" CSV consolidato mancante delle colonne richieste: {missing_cols}")

    if df.empty:
        raise ValueError(" Il DataFrame è vuoto. Controlla il file CSV di input.")

    if len(df) < 10:
        print(" Dati insufficienti nel file consolidato. Controlla il fetching e il consolidamento dei dati.")
        print(df.head())  # Mostra i dati disponibili per il debug
        raise ValueError(f" Il DataFrame ha meno di 10 righe. I dati sono insufficienti per calcolare gli indicatori per la coppia {pair}.")

    print("\n Verifica qualità dei dati...")
    df = validate_data_quality(df)
    
    # Aggiungi verifica freschezza dati
    freshness = check_data_freshness(df)
    
    # Se i dati non sono freschi, aggiorna i dati
    if not freshness:
        print("\n Tentativo di aggiornamento dati per garantire freschezza...")
        try:
            from forex_system.fetch.fetch_all_data import fetch_data_for_pair
            fetch_data_for_pair(pair)
            print(" Dati aggiornati con successo")
        except Exception as e:
            print(f" Impossibile aggiornare i dati: {e}")
        # if not freshness:
        #     print("❌ I dati non sono freschi: interrotto calcolo indicatori.")
        #     return None

    #print("\n📊 Statistiche dopo la pulizia:")
    #print(f"Righe totali: {len(df)}")
    #print("Colonne nel DataFrame:")
    for col in df.columns:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            print(f"- {col}: {null_count} valori nulli")
    # Indicatori
    df = calculate_fibonacci_levels(df)
    #print(" Dopo Fibonacci:", df[['timestamp', 'Fibonacci']].head(3))

    df = calculate_rsi(df)
    #print(" Dopo RSI:", df[['timestamp', 'RSI']].head(3))

    df = calculate_sma_atr(df)
    #print(" Dopo SMA e ATR:", df[['timestamp', 'SMA', 'ATR']].head(3))

    df = calculate_support_resistance(df)
    #print(" Dopo Supporto e Resistenza:", df[['timestamp', 'support', 'resistance']].head(3))

    df = calculate_wyckoff_phases(df)
    #print(" Dopo Wyckoff:", df[['timestamp', 'wyckoff_phase']].head(3))

    df = calculate_ml_indicator(df, pair, MODEL_DIR)
    # print(f"[ML DEBUG] {pair} - Controllo finale colonne: {df.columns[-5:].tolist()}")
    #print(" Dopo ML Indicator:", df[['timestamp', 'ML_TP', 'ML_SL']].head(3))

    # Sostituisci NaN in ML_TP e ML_SL con valori predefiniti
    df['ML_TP'] = pd.to_numeric(df['ML_TP'], errors='coerce').fillna(0)
    df['ML_SL'] = pd.to_numeric(df['ML_SL'], errors='coerce').fillna(0)

    # Sostituisci NaN nelle colonne calcolate con valori predefiniti
    calculated_columns = ['SMA', 'ATR', 'RSI', 'support', 'resistance', 'Fibonacci', 'wyckoff_phase', 'ML_TP', 'ML_SL']
    for col in calculated_columns:
        if col in df.columns:
            df[col] = df[col].fillna(0)  # Sostituisci NaN con 0

    # Rimuovi righe con valori NaN solo nelle colonne calcolate
    df[calculated_columns] = df[calculated_columns].fillna(0)
    print(" Righe eliminate per NaN:", df[calculated_columns].isna().any(axis=1).sum())
    # print(" Dopo dropna:", df.head(3))

    if df.empty:
        raise ValueError(f" Il DataFrame degli indicatori è vuoto dopo aver rimosso i valori NaN per la coppia {pair}.")

    #print(" DataFrame finale prima del salvataggio:")
    #print(df.head(3))
    #print(" Numero righe nel DataFrame finale:", len(df))

    indicators_csv = os.path.join(DATA_DIR, f"indicators_{pair}.csv")
    # Check score columns for all zeros or NaNs
    score_columns = ['RSI_score', 'SMA_score', 'Fibonacci_score', 'support_resistance_score', 'wyckoff_score', 'ML_CONFIDENCE_SCORE']
    for col in score_columns:
        if col in df.columns:
            if df[col].isnull().all():
                print(f" Tutti i valori sono NaN in {col}")
            elif (df[col] == 0).all():
                print(f" Tutti i valori sono 0 in {col}")

    df.to_csv(indicators_csv, index=False)

    print(f"Tutti gli indicatori calcolati e salvati: {indicators_csv}")

    print(f"\n{Style.BRIGHT}{Fore.YELLOW} ------------ Verifica indicatori disponibili per il training: ------------ {Style.RESET_ALL}")
    for col in score_columns:
        if col not in df.columns:
            print(f" Mancante: {col}")
        elif df[col].isnull().all():
            print(f" Tutti i valori NaN in {col}")
        elif (df[col] == 0).all():
            print(f" Tutti i valori 0 in {col}")
        else:
            print(f" Valido: {col}")

    return df

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        calculate_all_indicators(sys.argv[1])
    else:
        print(" Specifica la coppia da analizzare. Esempio: python loader.py EURUSD")


