import time
from update_and_train import fetch_data_for_pair, train_model_for_pair
from main import get_live_data
from forex_system.merge_data import consolidate_csv_data
from forex_system.indicators.loader import calculate_all_indicators
from forex_system.indicators.final_decision import make_final_prediction
import pandas as pd
import os
from datetime import datetime

STANDARD_PAIRS = [
    "AUDCAD",
    "AUDUSD",
    "CADCHF",
    "EURAUD",
    "EURCAD",
    "EURCHF",
    "EURGBP",
    "EURNZD",
    "EURUSD", 
    "GBPAUD",
    "GBPCAD",
    "GBPCHF",
    "GBPUSD", 
    "NZDUSD",
    "USDCAD",
    "USDCHF",
    "USDJPY",     
    ]

def loop_prediction(interval_sec=600):
    while True:
        now_utc = datetime.utcnow()
        day = now_utc.weekday()
        hour = now_utc.hour

        # Controllo mercato chiuso
        if (day == 4 and hour >= 22) or (day == 5) or (day == 6 and hour < 22):
            print(f" Mercati Forex CHIUSI (UTC {now_utc.strftime('%A %H:%M')}) → attendo apertura...")
            print(f" Attesa di {interval_sec // 60} minuti...\n")
            time.sleep(interval_sec)
            continue

        print(f"\n Loop di predizione avviato alle {now_utc}")

        for pair in STANDARD_PAIRS:
            try:
                print(f"\n Aggiornamento per {pair}")
                fetch_data_for_pair(pair)
                consolidate_csv_data(pair)
                indicators_df = calculate_all_indicators(pair)
                train_model_for_pair(pair, indicators_df)

                current_price = get_live_data(pair)['close'].iloc[-1]

                action, tp, sl, indicators_evaluation = make_final_prediction(
                    pair, indicators_df, live_price=current_price
                )

                prediction_data = {
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "pair": pair,
                    "action": action,
                    "entry_price": round(current_price, 5),
                    "tp": round(tp, 5) if isinstance(tp, (int, float)) else None,
                    "sl": round(sl, 5) if isinstance(sl, (int, float)) else None,
                    "confidence": indicators_evaluation.get("Confidence", 1.0),
                    "rsi": indicators_evaluation.get("RSI", "N/A"),
                    "wyckoff": indicators_evaluation.get("Wyckoff", "N/A"),
                    "trend_strength": indicators_evaluation.get("Trend Strength", "N/A")
                }

                log_path = os.path.join("log", "predictions")
                os.makedirs(log_path, exist_ok=True)
                file_path = os.path.join(log_path, f"market_prediction_{pair}.csv")

                df = pd.DataFrame([prediction_data])
                df.to_csv(file_path, mode='a', header=not os.path.exists(file_path), index=False)

                print(f" Predizione salvata per {pair} in {file_path}")
            except Exception as e:
                print(f" Errore su {pair}: {e}")

        print(f"\n Attesa di {interval_sec // 60} minuti...\n")
        time.sleep(interval_sec)

if __name__ == "__main__":
    loop_prediction()
