# import pandas as pd

# def calculate_fibonacci_levels(df):
#     if not isinstance(df, pd.DataFrame):
#         raise ValueError("L'input deve essere un DataFrame di pandas.")

#     recent = df.tail(100)

#     max_price = recent['close'].max()
#     min_price = recent['close'].min()
#     diff = max_price - min_price

#     df['fib_0.0'] = min_price
#     df['fib_0.236'] = min_price + 0.236 * diff
#     df['fib_0.382'] = min_price + 0.382 * diff
#     df['fib_0.5'] = min_price + 0.5 * diff
#     df['fib_0.618'] = min_price + 0.618 * diff
#     df['fib_0.786'] = min_price + 0.786 * diff
#     df['fib_1.0'] = max_price
#     df['fib_1.272'] = max_price + 0.272 * diff
#     df['fib_1.618'] = max_price + 0.618 * diff
#     df['fib_-0.272'] = min_price - 0.272 * diff

#     if 'close' in df.columns:
#         last_close = df['close'].iloc[-1]
#         for level in ['fib_0.0', 'fib_0.236', 'fib_0.382', 'fib_0.5', 'fib_0.618', 'fib_0.786', 'fib_1.0', 'fib_1.272', 'fib_1.618', 'fib_-0.272']:
#             norm_col = level + '_norm'
#             df[norm_col] = (last_close - df[level]) / diff

#     # Esempio di calcolo dei livelli di Fibonacci
#     if 'high' in df.columns and 'low' in df.columns:
#         df['Fibonacci'] = (df['high'] + df['low']) / 2  # Calcolo semplificato
#     else:
#         raise ValueError("Colonne 'high' e 'low' mancanti per il calcolo di Fibonacci.")
#     #print("📊 Dopo il calcolo di Fibonacci:", df[['timestamp', 'Fibonacci']].head(3))

#     return df  # Assicurati di restituire sempre un DataFrame

import pandas as pd

def calculate_fibonacci_levels(df):
    if not isinstance(df, pd.DataFrame):
        raise ValueError("L'input deve essere un DataFrame di pandas.")

    recent = df.tail(100)

    max_price = recent['close'].max()
    min_price = recent['close'].min()
    diff = max_price - min_price
    if diff == 0:
        diff = 1e-10  # prevenzione

    levels = {
        'fib_0.0': min_price,
        'fib_0.236': min_price + 0.236 * diff,
        'fib_0.382': min_price + 0.382 * diff,
        'fib_0.5': min_price + 0.5 * diff,
        'fib_0.618': min_price + 0.618 * diff,
        'fib_0.786': min_price + 0.786 * diff,
        'fib_1.0': max_price,
        'fib_1.272': max_price + 0.272 * diff,
        'fib_1.618': max_price + 0.618 * diff,
        'fib_-0.272': min_price - 0.272 * diff
    }

    for key, val in levels.items():
        df[key] = val
        df[key + '_norm'] = (df['close'] - val) / diff

    if 'high' in df.columns and 'low' in df.columns:
        df['Fibonacci'] = (df['high'] + df['low']) / 2
    else:
        raise ValueError("Colonne 'high' e 'low' mancanti per il calcolo di Fibonacci.")

    # Calcolo media dei livelli centrali per normalizzazione
    central_levels = ['fib_0.236', 'fib_0.382', 'fib_0.5', 'fib_0.618', 'fib_0.786']
    df["fibonacci_norm"] = df[central_levels].mean(axis=1)

    # Calcolo score finale: massimo punteggio se vicino al livello centrale
    df["Fibonacci_score"] = df["fibonacci_norm"].clip(0, 1)

    return df
