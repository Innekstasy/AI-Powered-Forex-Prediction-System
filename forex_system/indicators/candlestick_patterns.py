import pandas as pd

def detect_candlestick_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analizza gli ultimi 3 pattern di candela e aggiunge colonne booleane per pattern noti.
    Richiede colonne: Open, High, Low, Close (case-insensitive).
    """

    df = df.copy()
    df.columns = [col.lower() for col in df.columns]  # Normalizza header

    # Pattern placeholders
    df['bullish_engulfing'] = False
    df['bearish_engulfing'] = False
    df['morning_star'] = False
    df['evening_star'] = False
    df['doji'] = False
    df['hammer'] = False
    df['inverted_hammer'] = False

    for i in range(2, len(df)):
        o1, h1, l1, c1 = df.loc[i-2, ['open', 'high', 'low', 'close']]
        o2, h2, l2, c2 = df.loc[i-1, ['open', 'high', 'low', 'close']]
        o3, h3, l3, c3 = df.loc[i, ['open', 'high', 'low', 'close']]

        # Doji
        body = abs(c3 - o3)
        range_candle = h3 - l3
        df.at[i, 'doji'] = body <= 0.1 * range_candle

        # Bullish Engulfing
        if c2 < o2 and c3 > o3 and o3 < c2 and c3 > o2:
            df.at[i, 'bullish_engulfing'] = True

        # Bearish Engulfing
        if c2 > o2 and c3 < o3 and o3 > c2 and c3 < o2:
            df.at[i, 'bearish_engulfing'] = True

        # Morning Star
        cond = (
            c1 < o1 and
            abs(c2 - o2) < 0.3 * (h2 - l2) and
            c3 > o3 and c3 > (o1 + c1) / 2
        )
        if cond:
            df.at[i, 'morning_star'] = True

        # Evening Star
        cond = (
            c1 > o1 and
            abs(c2 - o2) < 0.3 * (h2 - l2) and
            c3 < o3 and c3 < (o1 + c1) / 2
        )
        if cond:
            df.at[i, 'evening_star'] = True

        # Hammer
        body = abs(c3 - o3)
        lower_shadow = o3 - l3 if c3 > o3 else c3 - l3
        upper_shadow = h3 - c3 if c3 > o3 else h3 - o3
        if lower_shadow > 2 * body and upper_shadow < 0.5 * body:
            df.at[i, 'hammer'] = True

        # Inverted Hammer
        if upper_shadow > 2 * body and lower_shadow < 0.5 * body:
            df.at[i, 'inverted_hammer'] = True

    return df
 
