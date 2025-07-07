# import pandas as pd

# def calculate_rsi(df, period=14):
#     delta = df['close'].diff()
#     gain = delta.where(delta > 0, 0)
#     loss = -delta.where(delta < 0, 0)

#     avg_gain = gain.rolling(window=period).mean()
#     avg_loss = loss.rolling(window=period).mean()

#     rs = avg_gain / avg_loss
#     df['RSI'] = 100 - (100 / (1 + rs))
#     df['RSI'] = df['RSI'].bfill().fillna(50)  # compatibile con future versioni

#     return df
import pandas as pd

def calculate_rsi(df, period=14):
    if 'close' not in df.columns:
        raise ValueError("Colonna 'close' mancante per il calcolo RSI")

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    # Protezione contro divisioni per zero
    avg_loss_replaced = avg_loss.mask(avg_loss == 0).bfill().fillna(1e-10)
    rs = avg_gain / avg_loss_replaced

    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].bfill().fillna(50)

    # RSI normalizzato (0-1 range)
    df['RSI_norm'] = (df['RSI'] / 100).clip(0, 1).fillna(0.5)

    # Calcolo dello score RSI: se RSI_norm > 0.55 => segnale BUY, se < 0.45 => SELL, altrimenti HOLD
    df['RSI_score'] = 0  # Default HOLD
    df.loc[df['RSI_norm'] > 0.55, 'RSI_score'] = 1   # BUY
    df.loc[df['RSI_norm'] < 0.45, 'RSI_score'] = -1  # SELL
    
    return df
