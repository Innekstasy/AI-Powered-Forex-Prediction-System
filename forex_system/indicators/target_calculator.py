# forex_system/strategy/target_calculator.py

def calculate_reliability(tp, sl, last_close, trend):
    if tp is None or sl is None:
        return 0.0

    # Converti i 15 pips in decimali (es. 0.0015)
    pip_size = 0.0001 if last_close < 3 else 0.01  # es. 0.01 per JPY
    pips_threshold = 15 * pip_size

    if trend == "BULLISH":
        tp_score = max(0, (tp - last_close) / pips_threshold)
        sl_score = max(0, (last_close - sl) / pips_threshold)
    else:
        tp_score = max(0, (last_close - tp) / pips_threshold)
        sl_score = max(0, (sl - last_close) / pips_threshold)

    return min((tp_score + sl_score) / 2, 1.0)

def weighted_mean(values, methods, reliabilities, methods_weight):
    valid = [(v, methods_weight[m] * r) for v, m, r in zip(values, methods, reliabilities) if v is not None]
    if not valid:
        return None
    total_weight = sum(w for v, w in valid)
    return round(sum(v * w for v, w in valid) / total_weight, 5)
