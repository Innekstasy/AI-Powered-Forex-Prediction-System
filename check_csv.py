import os
import glob
import pandas as pd
from datetime import datetime
import json
import yfinance as yf
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from collections import defaultdict

def validate_trade_outcome(trade, max_lookback_days=30):
    """Verifica il reale outcome del trade analizzando i dati storici"""
    try:
        trade_time = pd.to_datetime(trade['timestamp'])
        end_time = min(datetime.now(), trade_time + pd.Timedelta(days=max_lookback_days))
        
        # Calcola pips per il trade
        pip_value = 0.0001
        tp_pips = abs(float(trade['tp']) - float(trade['current_price'])) / pip_value
        sl_pips = abs(float(trade['sl']) - float(trade['current_price'])) / pip_value
        
        symbol = f"{trade['pair']}=X"
        hist = yf.download(symbol, start=trade_time, end=end_time, interval='5m', progress=False)
        
        if hist.empty:
            return "DATI_MANCANTI", 0

        try:
            entry_price = float(trade['current_price'])
            tp = float(trade['tp'])
            sl = float(trade['sl'])
        except (ValueError, TypeError, KeyError) as e:
            return f"ERRORE_VALORI: {str(e)}", 0

        # entry_price = float(trade['current_price'])
        # tp = float(trade['tp'])
        # sl = float(trade['sl'])
        
        for idx, row in hist.iterrows():
            high = float(row['High'].item())
            low = float(row['Low'].item())

            if trade['action'] == 'BUY':
                if high >= tp:
                    return f"TP_REALE ({idx})", tp_pips
                if low <= sl:
                    return f"SL_REALE ({idx})", -sl_pips
            else:  # SELL
                if low <= tp:
                    return f"TP_REALE ({idx})", tp_pips
                if high >= sl:
                    return f"SL_REALE ({idx})", -sl_pips
                    
        return "ANCORA_VALIDO", 0
        
    except Exception as e:
        return f"ERRORE: {str(e)}", 0

def analyze_prediction_files():
    """Analizza i file delle predizioni per verificare incongruenze"""
    print("\n ANALISI FILE PREDIZIONI")
    print("=" * 50)
    
    prediction_files = glob.glob("log/predictions/market_prediction_*.csv")
    if not prediction_files:
        print(" Nessun file di predizione trovato!")
        return
        
    all_trades = []
    problematic_files = []
    pair_results = defaultdict(lambda: {'TP': 0, 'SL': 0, 'PENDING': 0, 'PIPS': 0})
    
    for file in prediction_files:
        try:
            df = pd.read_csv(file)
            filename = os.path.basename(file)
            print(f"\n Analisi file: {filename}")
            
            required_fields = {'tp', 'sl', 'current_price', 'pair', 'action', 'timestamp'}
            missing_cols = required_fields - set(df.columns)
            if missing_cols:
                print(f" File {filename} manca delle colonne obbligatorie: {missing_cols}")
                problematic_files.append(file)
                continue

            for _, trade in df.iterrows():
                outcome, pips = validate_trade_outcome(trade)
                pair = trade['pair']
                
                print(f"      Trade {pair}:")
                print(f"      Outcome: {outcome}")
                print(f"      Pips: {pips:.1f}")
                
                pair_results[pair]['PIPS'] += pips
                if 'TP_REALE' in outcome:
                    pair_results[pair]['TP'] += 1
                elif 'SL_REALE' in outcome:
                    pair_results[pair]['SL'] += 1
                else:
                    pair_results[pair]['PENDING'] += 1
                    
            all_trades.append(df)
            
        except Exception as e:
            print(f" Errore: {str(e)}")
            problematic_files.append(file)
    
    # Report finale
    print("\n REPORT FINALE")
    print("=" * 50)
    
    total_pips = 0
    total_trades = 0
    
    for pair, results in pair_results.items():
        total = results['TP'] + results['SL']
        win_rate = (results['TP'] / total * 100) if total > 0 else 0
        
        print(f"\n{pair}:")
        print(f"   Totale trade: {total}")
        print(f"   TP: {results['TP']}")
        print(f"   SL: {results['SL']}")
        print(f"   Pending: {results['PENDING']}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Pips: {results['PIPS']:.1f}")
        
        total_pips += results['PIPS']
        total_trades += total
    
    print("\n PERFORMANCE COMPLESSIVA")
    print(f"Totale trades: {total_trades}")
    print(f"Profitto totale: {total_pips:.1f} pips")
    print(f"Media per trade: {(total_pips/total_trades if total_trades > 0 else 0):.1f} pips")

def main():
    print(" Avvio verifica CSV trading system")
    analyze_prediction_files()

if __name__ == "__main__":
    main()