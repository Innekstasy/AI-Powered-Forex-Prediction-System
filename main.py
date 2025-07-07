# main.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import pandas as pd
from forex_system.fetch.fetch_all_data import fetch_data_for_pair
from forex_system.merge_data import consolidate_csv_data
from forex_system.indicators.loader import calculate_all_indicators
from forex_system.trainer import train_model_for_pair
from forex_system.indicators.final_decision import make_final_prediction
from update_and_train import save_custom_pair
import yfinance as yf
from datetime import datetime, timezone
from colorama import init, Fore, Style
init()  # Abilita il supporto su Windows

PAIR_OPTIONS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "USDCHF",
    "AUDUSD"
]

CONFIG_PATH = os.path.join('srv', 'last_selected_pair.json')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def select_pair():
    print("\n=== Selezione Coppia Forex ===")
    for idx, pair in enumerate(PAIR_OPTIONS, 1):
        print(f"{idx}. {pair}")
    print(f"{len(PAIR_OPTIONS) + 1}. Inserisci manualmente una coppia")

    try:
        choice = input("\nInserisci il numero corrispondente o la coppia manualmente: ")

        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(PAIR_OPTIONS):
                pair = PAIR_OPTIONS[choice - 1]
            elif choice == len(PAIR_OPTIONS) + 1:
                pair = input("Inserisci la coppia manualmente (es. EURUSD): ").upper()
            else:
                raise ValueError("Scelta non valida.")
        else:
            pair = choice.upper()  # Tratta l'input come coppia se non è un numero

        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump({"last_selected_pair": pair}, f)

        # Salva la coppia personalizzata
        save_custom_pair(pair)

        return pair
    except ValueError as e:
        print(f"\n Errore: {str(e)}")
        sys.exit(1)

def get_live_data(pair):
    """Get live data from Yahoo Finance"""
    try:
        print(f"\n Fetching live data for {pair}...")
        ticker = yf.Ticker(f"{pair}=X")
        data = ticker.history(period="1d", interval="1m")
        
        if not data.empty:
            df = data.reset_index()
            df = df.rename(columns={
                'Datetime': 'timestamp',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            return df
        else:
            raise ValueError("No data received from Yahoo Finance")
    except Exception as e:
        print(f" Error fetching live data: {e}")
        return None

def main():
    try:
        # Seleziona la coppia Forex
        pair = select_pair()

        # Verifica se il mercato è aperto (domenica 22 → venerdì 22 UTC)
        now_utc = datetime.utcnow()
        day = now_utc.weekday()  # 0 = lunedì, 6 = domenica
        hour = now_utc.hour

        print(f"\n Ora attuale UTC: {now_utc.strftime('%A %H:%M')}")

        if (day == 4 and hour >= 22) or (day == 5) or (day == 6 and hour < 22):
            print(f"\n Mercati Forex CHIUSI (UTC {now_utc.strftime('%A %H:%M')}) → riprova quando sono aperti.")
            sys.exit(0)

        print(f"\n Coppia selezionata: {pair}")

        # Get live data from Yahoo
        print("\n Recupero dati live da Yahoo Finance...")
        live_df = get_live_data(pair)
        if live_df is None:
            raise ValueError("❌ Impossibile ottenere dati live da Yahoo")

        current_price = live_df['close'].iloc[-1]
        print(f" Prezzo attuale: {current_price:.5f}")

        # Controlla e scarica i dati se non esistono
        print(f"\n{Style.BRIGHT}{Fore.YELLOW} --------- Verifica dati consolidati... --------- {Style.RESET_ALL}")
        try:
            consolidate_csv_data(pair)
        except FileNotFoundError:
            print(f" Dati non trovati per {pair}. Avvio del fetch...")
            fetch_data_for_pair(pair, mode="historical")
            consolidate_csv_data(pair)

        # Calcolo degli indicatori tecnici
        print("\n Calcolo indicatori tecnici...")
        indicators_df = calculate_all_indicators(pair)

        # Make prediction using live price
        print(f"\n{Style.BRIGHT}{Fore.YELLOW} ============ Generazione predizione... ============ {Style.RESET_ALL}")
        print(" Avvio processo decisionale finale (make_final_prediction)...")
        try:
            action, tp, sl, indicators_evaluation = make_final_prediction(
                pair, 
                indicators_df,
                live_price=current_price  # Pass live price here
            )
            if action == "HOLD":
                print(f" Nessuna operazione confermata per {pair}: azione HOLD per bassa confidence.")
            elif tp is None or sl is None:
                print(f" Nessun segnale valido su {pair}: TP o SL non sono stati generati. Il modello potrebbe non avere dati sufficienti o la confidence è troppo bassa.")

            # if action and tp and sl:
            #     print(f"Azione: {action}, TP: {tp:.5f}, SL: {sl:.5f}")
            # else:
            #     print(" Nessuna azione operativa: il sistema ha deciso di ignorare il segnale.")

            # Output finale
            print(f"\n{Style.BRIGHT}{Fore.GREEN} ============ Riepilogo Analisi: ============ {Style.RESET_ALL}")
            print(f"Coppia: {pair}")
            print(f"Prezzo live: {current_price:.5f}")
            print(f"Azione consigliata: {action}")
            # print(f"Take Profit: {tp:.5f}")
            # print(f"Stop Loss: {sl:.5f}")

            if isinstance(tp, (int, float)) and isinstance(sl, (int, float)):
                print(f"Take Profit: {tp:.5f}")
                print(f"Stop Loss: {sl:.5f}")
            else:
                print(f"DEBUG: tp={tp}, sl={sl}, type(tp)={type(tp)}, type(sl)={type(sl)}")
                print(" TP o SL non validi (None o non numerici).")

            print(f"\n{Style.BRIGHT}{Fore.YELLOW} ------------ Indicatori principali: ------------ {Style.RESET_ALL}")
            for indicator, value in indicators_evaluation.items():
                print(f"{indicator}: {value}")
            
            # 🔁 Salvataggio della predizione in CSV

            prediction_data = {
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "pair": pair,
                "action": action,
                "entry_price": round(current_price, 5),
                "tp": round(float(tp), 5) if isinstance(tp, (int, float)) and not pd.isna(tp) else None,
                "sl": round(float(sl), 5) if isinstance(sl, (int, float)) and not pd.isna(sl) else None,

                # "tp": round(tp, 5) if isinstance(tp, (int, float)) else None,
                # "sl": round(sl, 5) if isinstance(sl, (int, float)) else None,
                "confidence": indicators_evaluation.get("Confidence", 1.0),
                "ML_CONFIDENCE_SCORE": indicators_evaluation.get("ML_CONFIDENCE_SCORE"),  # ✅ Aggiunto

                "rsi": indicators_evaluation.get("RSI", "N/A"),
                "wyckoff": indicators_evaluation.get("Wyckoff", "N/A"),
                "trend_strength": indicators_evaluation.get("Trend Strength", "N/A")
            }

            log_path = os.path.join("log", "predictions")
            os.makedirs(log_path, exist_ok=True)
            file_path = os.path.join(log_path, f"market_prediction_{pair}.csv")

            df = pd.DataFrame([prediction_data])
            df.to_csv(file_path, mode='a', header=not os.path.exists(file_path), index=False)

            print(f"\n Predizione salvata in {file_path}")

        except FileNotFoundError:
            print(f" Modello non trovato per {pair}. Attendere il prossimo ciclo di update_and_train per la generazione del modello.")

    except Exception as e:
        print(f"\n Errore: {str(e)}")
        return

    print("\n Analisi completata!")

if __name__ == "__main__":
    main()

