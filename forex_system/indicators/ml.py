#from forex_system.trainer import load_model
from forex_system.model_utils import load_model

# def evaluate_ml_confidence(pred_tp, pred_sl, current_price, rsi, wyckoff, sma):
#     """
#     Valuta qualitativamente e quantitativamente la coerenza delle predizioni TP/SL.
#     """
#     market_bias = 0

#     # RSI contribution
#     if rsi > 60:
#         market_bias += 0.3
#     elif rsi < 40:
#         market_bias -= 0.3

#     # Wyckoff contribution
#     if wyckoff == "markup":
#         market_bias += 0.4
#     elif wyckoff == "markdown":
#         market_bias -= 0.4
#     elif wyckoff == "accumulation":
#         market_bias += 0.1
#     elif wyckoff == "distribution":
#         market_bias -= 0.1

#     # SMA vs price
#     if current_price > sma:
#         market_bias += 0.2
#     elif current_price < sma:
#         market_bias -= 0.2

#     bias_score = round(market_bias, 2)

#     # TP direction check
#     if pred_tp > current_price and bias_score > 0.3:
#         quality = "HIGH"
#     elif pred_tp < current_price and bias_score < -0.3:
#         quality = "HIGH"
#     elif abs(bias_score) < 0.1:
#         quality = "LOW"
#     else:
#         quality = "MEDIUM"

#     return quality, bias_score

def evaluate_ml_confidence(pred_tp, pred_sl, current_price, rsi, wyckoff, sma):
    market_bias = 0

    if rsi > 60:
        market_bias += 0.3
    elif rsi < 40:
        market_bias -= 0.3

    if wyckoff == "markup":
        market_bias += 0.4
    elif wyckoff == "markdown":
        market_bias -= 0.4
    elif wyckoff == "accumulation":
        market_bias += 0.1
    elif wyckoff == "distribution":
        market_bias -= 0.1

    if current_price > sma:
        market_bias += 0.2
    elif current_price < sma:
        market_bias -= 0.2

    bias_score = round(market_bias, 2)
    confidence_score = min(max(abs(bias_score), 0), 1.0)  # normalizzato [0, 1]

    return confidence_score, bias_score

def predict_tp_sl_ml(df, pair):
    model = load_model(pair)

    # Solo le colonne richieste dal modello devono essere non-NaN
    model_input_cols = model.feature_names_in_ if hasattr(model, "feature_names_in_") else df.columns
    df_clean = df.dropna(subset=model_input_cols)
    # print(f"[ML DEBUG] {pair} - Colonne richieste dal modello: {model_input_cols}")
    # print(f"[ML DEBUG] {pair} - Righe disponibili dopo dropna: {len(df_clean)}")
    if df_clean.empty:
        raise ValueError("Dati insufficienti per il modello (tutti NaN nelle colonne rilevanti)")

    last_row = df_clean.iloc[-1:].drop(columns=['RSI', 'SMA', 'ATR'], errors='ignore')

    try:
        if last_row.empty or 'close' not in last_row.columns:
            return {'tp': None, 'sl': None}

        tp_pred, sl_pred = model.predict(last_row)[0]

        tp = round(tp_pred, 5)
        sl = round(sl_pred, 5)

        # ✅ Valutazione semplice del trend per coerenza
        if last_row.empty or 'close' not in last_row.columns:
            return {'tp': None, 'sl': None}
        # last_close = last_row['close'].values[0]
        if 'close' in last_row.columns and not last_row['close'].empty:
            last_close = last_row['close'].values[0]
        else:
            raise ValueError("Colonna 'close' mancante o vuota nel last_row")

        if tp == last_close:
            tp += 0.002  # Forziamo una distanza minima
        if sl == last_close:
            sl -= 0.002

        return {'tp': tp, 'sl': sl}
    except Exception:
        return {'tp': None, 'sl': None}
    
def calculate_ml_indicator(df, pair, model_dir):
    try:
        prediction = predict_tp_sl_ml(df, pair)
        # print(f"[ML DEBUG] {pair} - Predizione TP/SL: {prediction}")
        df['ML_TP'] = prediction['tp']
        df['ML_SL'] = prediction['sl']

        # Recupero dati per coerenza
        df_nonan = df.dropna(subset=["close", "RSI", "SMA", "ATR", "wyckoff_phase"])
        if df_nonan.empty:
            raise ValueError(f"Nessun dato valido per la coppia {pair} dopo il dropna()")
        last_row = df_nonan.iloc[-1]
        rsi = last_row.get("RSI", 50)
        sma = last_row.get("SMA", last_row["close"])
        wyckoff = last_row.get("wyckoff_phase", "neutral")
        current_price = last_row["close"]

        if prediction['tp'] is None or prediction['sl'] is None:
            # print(f"[ML DEBUG] {pair} - Predizione non valida: TP={prediction['tp']}, SL={prediction['sl']}")
            df['ML_TP'] = None
            df['ML_SL'] = None
            df['ML_CONFIDENCE_SCORE'] = 0
            df['ML_MARKET_BIAS_SCORE'] = 0
            return df

        confidence_score, bias_score = evaluate_ml_confidence(
            prediction['tp'], prediction['sl'], current_price, rsi, wyckoff, sma
        )

        df['ML_CONFIDENCE_SCORE'] = confidence_score
        df['ML_MARKET_BIAS_SCORE'] = bias_score

    except Exception as e:
        print(f"Errore ML su {pair}: {e}")
        df['ML_TP'] = None
        df['ML_SL'] = None
        df['ML_CONFIDENCE_QUALITY'] = "LOW"
        df['ML_MARKET_BIAS_SCORE'] = 0

    return df
