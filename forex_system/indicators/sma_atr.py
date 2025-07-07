# import numpy as np

# def calculate_true_range(high, low, previous_close):
#     """Calcola il True Range per un singolo periodo"""
#     return max(
#         high - low,  # Current High - Current Low
#         abs(high - previous_close),  # Current High - Previous Close
#         abs(low - previous_close)  # Current Low - Previous Close
#     )

# def calculate_sma_atr(df, period=14):
#     """
#     Calcola SMA e ATR secondo la formula di Wilder
#     :param df: DataFrame con colonne 'high', 'low', 'close'
#     :param period: Periodo per il calcolo (default: 14)
#     :return: DataFrame con colonne aggiunte 'SMA' e 'ATR'
#     """
#     # Calcolo SMA
#     df['SMA'] = df['close'].rolling(window=period).mean()
    
#     # Calcolo True Range
#     true_range = []
#     for i in range(len(df)):
#         if i == 0:
#             true_range.append(df['high'].iloc[0] - df['low'].iloc[0])
#         else:
#             tr = calculate_true_range(
#                 df['high'].iloc[i],
#                 df['low'].iloc[i],
#                 df['close'].iloc[i-1]
#             )
#             true_range.append(tr)
    
#     df['TR'] = true_range
    
#     # Calcolo ATR usando la formula di Wilder
#     df['ATR'] = df['TR'].rolling(window=period).apply(
#     lambda x: np.sum(x) / period if len(x) == period else np.nan
#     )
#     df['ATR'] = df['ATR'].bfill().fillna(0)  # compatibile con future versioni

#     # Pulizia dati
#     df = df.drop('TR', axis=1)  # Rimuovi colonna temporanea TR
    
#     # Log per debugging
#     #print("\n📊 Statistiche ATR:")
#     #print(f"Media ATR: {df['ATR'].mean():.5f}")
#     #print(f"Max ATR: {df['ATR'].max():.5f}")
#     #print(f"Min ATR: {df['ATR'].min():.5f}")
    
#     return df

import numpy as np
import pandas as pd

def calculate_true_range(high, low, previous_close):
    """Calcola il True Range per un singolo periodo"""
    return max(
        high - low,
        abs(high - previous_close),
        abs(low - previous_close)
    )

def calculate_sma_atr(df, period=14):
    """
    Calcola SMA e ATR secondo la formula di Wilder
    :param df: DataFrame con colonne 'high', 'low', 'close'
    :param period: Periodo per il calcolo (default: 14)
    :return: DataFrame con colonne aggiunte 'SMA' e 'ATR'
    """
    # Controllo colonne essenziali
    required_cols = {'high', 'low', 'close'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Il DataFrame deve contenere le colonne: {required_cols}")

    # Calcolo SMA
    df['SMA'] = df['close'].rolling(window=period).mean()

    # Calcolo True Range
    tr = [np.nan]  # primo elemento non calcolabile
    for i in range(1, len(df)):
        tr.append(calculate_true_range(
            df['high'].iloc[i],
            df['low'].iloc[i],
            df['close'].iloc[i - 1]
        ))
    df['TR'] = tr

    # Calcolo ATR con formula Wilder
    df['ATR'] = df['TR'].rolling(window=period).apply(
        lambda x: np.sum(x) / period if len(x) == period else np.nan,
        raw=True
    )

    # Calcolo primo valore utile di ATR manualmente se mancante
    if df['ATR'].isna().iloc[period] and not pd.isna(df['TR'].iloc[1:period+1]).any():
        df.at[period, 'ATR'] = np.mean(df['TR'].iloc[1:period+1])

    df['ATR'] = df['ATR'].bfill().fillna(0)  # riempie i rimanenti NaN solo se necessario

    # Rimuovi colonna temporanea
    df.drop('TR', axis=1, inplace=True)

    # Normalizzazione SMA e ATR
    df['SMA_norm'] = (df['close'] - df['SMA']) / df['SMA'].replace(0, 1e-10)
    df['ATR_norm'] = df['ATR'] / df['ATR'].replace(0, 1e-10)
    df['SMA_norm'] = df['SMA_norm'].clip(0, 1).fillna(0.5)
    df['ATR_norm'] = df['ATR_norm'].clip(0, 1).fillna(0.5)

    # Calcolo score per ATR e SMA
    df['SMA_score'] = 1 - abs(df['SMA_norm'] - 0.5) * 2  # punteggio massimo quando SMA_norm è vicino a 0.5
    df['ATR_score'] = 1 - abs(df['ATR_norm'] - 0.5) * 2  # punteggio massimo quando ATR_norm è vicino a 0.5

    # Clipping per evitare valori fuori [0,1]
    df['SMA_score'] = df['SMA_score'].clip(0, 1)
    df['ATR_score'] = df['ATR_score'].clip(0, 1)

    return df
