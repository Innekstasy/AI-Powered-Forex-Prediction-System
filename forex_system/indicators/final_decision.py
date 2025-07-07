import joblib
import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from datetime import datetime
from forex_system.indicators.ml import evaluate_ml_confidence
from datetime import timedelta
from colorama import init, Fore, Style
init()  # Abilita il supporto su Windows

def is_pending_expired(timestamp, max_hours=24):
    """Controlla se il segnale pending è scaduto"""
    trade_time = pd.to_datetime(timestamp)
    time_diff = datetime.now() - trade_time
    return time_diff > timedelta(hours=max_hours)

DATA_DIR = os.path.join("data")
MODEL_DIR = os.path.join("model")
PREDICTIONS_LOG_DIR = os.path.join("log", "predictions")

def evaluate_market_bias(rsi, wyckoff, sma, price):
    """
    Valuta il bias del mercato (bullish/bearish) in base agli indicatori principali.
    Ritorna un valore tra -1 (forte bearish) a +1 (forte bullish)
    """
    bias = 0

    # RSI
    if rsi > 60:
        bias += 0.3
    elif rsi < 40:
        bias -= 0.3

    # Wyckoff
    if wyckoff == "markup":
        bias += 0.4
    elif wyckoff == "markdown":
        bias -= 0.4
    elif wyckoff == "accumulation":
        bias += 0.1
    elif wyckoff == "distribution":
        bias -= 0.1

    # SMA vs current price
    if price > sma:
        bias += 0.2
    elif price < sma:
        bias -= 0.2

    return round(bias, 2)

def make_final_prediction(pair, indicators_df, live_price=None):
    # Load saved components
    model = joblib.load(os.path.join(MODEL_DIR, f"model_{pair}.pkl"))
    scaler = joblib.load(os.path.join(MODEL_DIR, f"scaler_{pair}.pkl"))
    required_columns = joblib.load(os.path.join(MODEL_DIR, f"columns_{pair}.pkl"))
    label_encoders = joblib.load(os.path.join(MODEL_DIR, f"encoders_{pair}.pkl"))

    # Get the last row for prediction
    last_row = indicators_df.iloc[-1:].copy()
    columns_to_drop = [col for col in last_row.columns if any(x in col for x in ['timestamp', 'ML_TP', 'ML_SL'])]
    features = last_row.drop(columns=columns_to_drop)

    for col, encoder in label_encoders.items():
        if col in features.columns:
            features[col] = encoder.transform(features[col].astype(str))

    for col in required_columns:
        if col not in features.columns:
            features[col] = 0

    features = features[required_columns]
    features_scaled = scaler.transform(features)
    prediction = model.predict(features_scaled)[0]
    print(f" Modello predizione grezza: {prediction} ({'BUY' if prediction == 1 else 'SELL'})")

    # Get live price or fallback
    current_price = live_price if live_price else last_row['close'].iloc[0]
    current_price = round(current_price, 5)

    if current_price <= 0 or pd.isna(current_price):
        print(" Prezzo corrente non valido per il calcolo di TP/SL.")
        return None, None, None, {"reason": "Invalid current_price"}


    # Indicator values
    rsi = last_row['RSI'].iloc[0]
    sma = last_row['SMA'].iloc[0]
    atr = last_row['ATR'].iloc[0]

    if atr is None or pd.isna(atr):
        print(" ATR non valido. Predizione interrotta.")
        return None, None, None, {"reason": "ATR invalid"}

    wyckoff = last_row['wyckoff_phase'].iloc[0]

    trend_strength = 3 if (rsi > 60 and wyckoff == 'markup') or (rsi < 40 and wyckoff == 'markdown') else 1
    market_bias = evaluate_market_bias(rsi, wyckoff, sma, current_price)
    print(f" Market Bias Indicator: {market_bias}")
    print(f" RSI: {rsi}, Wyckoff: {wyckoff}, Trend Strength: {trend_strength}")

    # Logica migliorata per TP/SL in funzione del trend
    if trend_strength > 2:  # trend forte rilevato
        max_sl_pips = 30
        sl_multiplier = 1.0
        tp_multiplier = 2.0
        print(f" Trend forte rilevato: SL esteso a {max_sl_pips} pips")
    else:
        if prediction == 1:  # BUY
            sl_multiplier = 0.5 if atr < 0.0003 else 0.8
            tp_multiplier = 0.8 if atr < 0.0003 else 1.2
        else:  # SELL
            sl_multiplier = 0.5 if atr < 0.0003 else 0.8
            tp_multiplier = 1.0 if atr < 0.0003 else 1.2
        max_sl_pips = 20

    # Verifica del segnale SELL con flag di rischio ottimizzato per intraday
    high_risk = False
    if prediction == 0:  # Potential SELL
        if rsi < 50 or wyckoff == 'accumulation':
            print(" Segnale SELL considerato ad alto rischio: RSI troppo basso o Wyckoff in accumulazione.")
            high_risk = True

    # Define action
    action = "BUY" if prediction == 1 else "SELL"

    def qualitative_confidence(prediction, wyckoff_phase):
        """
        Restituisce un'etichetta qualitativa basata sulla coerenza tra predizione e fase Wyckoff.
        """
        if prediction == 1 and wyckoff_phase == 'markup':
            return "HIGH"
        elif prediction == 0 and wyckoff_phase == 'markdown':
            return "HIGH"
        elif prediction == 1 and wyckoff_phase == 'accumulation':
            return "MEDIUM"
        elif prediction == 0 and wyckoff_phase == 'distribution':
            return "MEDIUM"
        elif wyckoff_phase == 'neutral':
            return "LOW"
        else:
            return "LOW"

    def quantitative_confidence_score(prediction, wyckoff_phase, rsi, high_risk, market_bias):
        """
        Restituisce uno score numerico di confidence basato su coerenza tra predizione e fase Wyckoff, RSI e rischio.
        """
        score = 0.5  # base neutral score

        # Aggiusta score in base alla coerenza tra predizione e fase Wyckoff
        if prediction == 1 and wyckoff_phase == 'markup':
            score += 0.3
        elif prediction == 0 and wyckoff_phase == 'markdown':
            score += 0.3
        elif prediction == 1 and wyckoff_phase == 'accumulation':
            score += 0.15
        elif prediction == 0 and wyckoff_phase == 'distribution':
            score += 0.15
        elif wyckoff_phase == 'neutral':
            score -= 0.1
        else:
            score -= 0.15

        # Penalizza se RSI non supporta la direzione
        if prediction == 1 and rsi < 50:
            score -= 0.1
        elif prediction == 0 and rsi > 50:
            score -= 0.1

        # Penalizza se segnale è considerato ad alto rischio
        if high_risk:
            score -= 0.2

        # Nuovo: premia o penalizza in base al bias
        if prediction == 1 and market_bias > 0.3:
            score += 0.2
        elif prediction == 0 and market_bias < -0.3:
            score += 0.2
        elif abs(market_bias) < 0.1:
            score -= 0.1
            
        return round(min(max(score, 0), 1), 2)

    # Calcolo aggregato della confidence usando i punteggi degli indicatori
    indicator_scores = []

    for col in ['RSI_score', 'SMA_score', 'wyckoff_score', 'support_resistance_score', 'Fibonacci_score', 'ML_CONFIDENCE_SCORE']:
        if col in last_row and pd.notna(last_row[col].iloc[0]):
            indicator_scores.append(last_row[col].iloc[0])

    if indicator_scores:
        confidence_score = round(sum(indicator_scores) / len(indicator_scores), 2)
    else:
        confidence_score = 0

    # Qualifica la confidence per logging
    if confidence_score > 0.7:
        confidence_level = "HIGH"
    elif confidence_score > 0.5:
        confidence_level = "MEDIUM"
    else:
        confidence_level = "LOW"

    # Blocca il segnale se la confidence aggregata è troppo bassa
    if confidence_score < 0.3:
        print(f"\n{Style.BRIGHT}{Fore.RED} Confidence troppo bassa ({confidence_score}) per confermare {action}. Cambio azione in HOLD. {Style.RESET_ALL}")
        action = "HOLD"

        return action, None, None, {
            "reason": "Low confidence",
            "confidence_score": confidence_score,
            "prediction": prediction,
            "wyckoff": wyckoff,
            "rsi": rsi
        }


    # Funzione per determinare il valore del pip in base al prezzo corrente
    def calculate_pip_value(price):
        if price >= 100:
            return 0.001  # Coppie come USD/JPY (3 decimali)
        elif price >= 1:
            return 0.0001  # Coppie come EUR/USD (5 decimali)
        else:
            return 0.0001  # Coppie come USD/CHF (4 decimali)


    # Calcolo dinamico del valore del pip
    pip_value = calculate_pip_value(current_price)
    min_sl_pips = 7
    min_tp_pips = 10

    # Ottimizzazione per operazioni Intraday/Swing
    pip_value = calculate_pip_value(current_price)

    if pip_value == 0 or pip_value is None or atr is None or pd.isna(atr):
        print(f" ERRORE: Impossibile calcolare TP/SL - pip_value={pip_value}, atr={atr}")
        return None, None, None, {
            "reason": "Invalid pip_value or ATR",
            "current_price": current_price,
            "atr": atr,
            "pip_value": pip_value
        }

    # print(f" DEBUG ATR: {atr}, pip_value: {pip_value}, sl_multiplier: {sl_multiplier}, tp_multiplier: {tp_multiplier}")
    
    # Calcolo dinamico di SL e TP ottimizzato per intraday/scalping
    sl_pips = max(min(round(atr * sl_multiplier / pip_value), max_sl_pips), 7)
    tp_pips = max(min(round(atr * tp_multiplier / pip_value), 20), 10)  # TP resta limitato
    
    if action == "BUY":
        sl = round(current_price - (sl_pips * pip_value), 5)
        tp = round(current_price + (tp_pips * pip_value), 5)
    else:
        sl = round(current_price + (sl_pips * pip_value), 5)
        tp = round(current_price - (tp_pips * pip_value), 5)

    if any(pd.isna(x) or x <= 0 for x in [tp, sl]):
        print(f" TP/SL generati non validi: TP={tp}, SL={sl}")
        return None, None, None, {"reason": "TP/SL calculated invalid"}

    print(f" Intraday/Swing TP/SL - Azione: {action}")
    print(f"ATR: {atr}, SL pips: {sl_pips}, TP pips: {tp_pips}")
    print(f"SL: {sl}, TP: {tp}")

    risk_label = "HIGH RISK" if high_risk else "NORMAL"

    
    indicators_evaluation = {
        "RSI": rsi,
        "SMA": sma,
        "ATR": atr,
        "Wyckoff": wyckoff
    }

    prediction_result = {
        "timestamp": datetime.now(),
        "pair": pair,
        "action": action,
        "current_price": current_price,
        "tp": tp,
        "sl": sl,
        "risk": risk_label,
        "indicators_evaluation": indicators_evaluation,
        "confidence": confidence_level,
        "confidence_score": confidence_score,
    }

    os.makedirs(PREDICTIONS_LOG_DIR, exist_ok=True)
    pred_csv = os.path.join(PREDICTIONS_LOG_DIR, f"market_prediction_{pair}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
    pd.DataFrame([prediction_result]).to_csv(pred_csv, index=False)

    if tp is None or sl is None:
        print(f" ERRORE DEBUG: TP={tp}, SL={sl}, current_price={current_price}, atr={atr}, pip_value={pip_value}")
        print(f" TP o SL non disponibili. Debug => current_price: {current_price}, atr: {atr}, pip_value: {pip_value}, tp_multiplier: {tp_multiplier}, sl_multiplier: {sl_multiplier}")
        return None, None, None, {"reason": "TP/SL undefined"}

    print(f"Predizione generata e salvata: {pred_csv}")
    print()
    print(f"Azione: {action}, TP: {tp:.5f}, SL: {sl:.5f}, Rischio: {risk_label}")
    print()

    # print(f"Azione: {action}, TP: {tp}, SL: {sl}, Rischio: {risk_label}")
    print(f"\n{Style.BRIGHT}{Fore.GREEN} ---------- Valutazione degli indicatori: ---------- {Style.RESET_ALL}")
    print(f"Confidence qualitativa: {confidence_level}")
    print(f"Confidence quantitativa: {confidence_score}")

    for key, value in indicators_evaluation.items():
        print(f"  {key}: {value}")
    
    indicators_evaluation["ML_CONFIDENCE_SCORE"] = confidence_score  # ✅ AGGIUNGI QUESTO
    return action, tp, sl, indicators_evaluation


if __name__ == "__main__":
    indicators_csv = os.path.join(DATA_DIR, "indicators_EURUSD.csv")
    indicators_df = pd.read_csv(indicators_csv)
    result = make_final_prediction("EURUSD", indicators_df)

    if result is not None:
        action, tp, sl, indicators = result
        if isinstance(tp, float) and isinstance(sl, float):
            print(f" Predizione: Azione: {action}, TP: {tp:.5f}, SL: {sl:.5f}")
        else:
            print(" TP o SL non validi (non numerici).")
    else:
        print(" Nessun risultato valido dalla predizione.")
