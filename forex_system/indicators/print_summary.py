def print_summary(pair, df, indicators, price_targets, final_action, final_tp, final_sl, confidence, notes):
    print("\n=== RISULTATO FINALE ===")
    print(f"Coppia Analizzata: {pair}")
    print(f"Ultima chiusura: {df['close'].iloc[-1]}")
    print(f"Trend: {price_targets['trend']}")
    print(f"RSI: {price_targets['rsi']:.2f}")
    print(f"TP (Take Profit): {final_tp}")
    print(f"SL (Stop Loss): {final_sl}")
    print(f"Azione Consigliata: {final_action}")
    print(f"Confidenza Segnale: {confidence}%")
    print(f"Note Votazione: {notes}")
    print("========================\n")
