# import pandas as pd

# def calculate_support_resistance(df):
#     # Verifica se df è un DataFrame, altrimenti solleva un'eccezione
#     if not isinstance(df, pd.DataFrame):
#         raise ValueError("L'input deve essere un DataFrame di pandas.")

#     # Verifica che il DataFrame contenga la colonna 'close'
#     if 'close' not in df.columns:
#         raise ValueError("Il DataFrame deve contenere la colonna 'close'.")

#     # Calcolo dei livelli di supporto e resistenza
#     recent = df.tail(100)
#     support = recent['close'].min()
#     resistance = recent['close'].max()

#     # Aggiunge i livelli di supporto e resistenza come nuove colonne
#     df['support'] = support
#     df['resistance'] = resistance

#     return df

import pandas as pd

def calculate_support_resistance(df):
    # Verifica input
    if not isinstance(df, pd.DataFrame):
        raise ValueError("L'input deve essere un DataFrame di pandas.")
    if 'close' not in df.columns:
        raise ValueError("Il DataFrame deve contenere la colonna 'close'.")

    # Finestra di analisi per la zona recente
    recent = df.tail(100)
    support = recent['close'].min()
    resistance = recent['close'].max()

    df['support'] = support
    df['resistance'] = resistance

    # Normalizzazione: posizione del prezzo tra supporto e resistenza
    range_val = resistance - support
    if range_val == 0:
        df['support_norm'] = 0.5
        df['resistance_norm'] = 0.5
        df['support_resistance_score'] = 0.5
    else:
        df['support_norm'] = (df['close'] - support) / range_val
        df['resistance_norm'] = (resistance - df['close']) / range_val
        # Score: se vicino al supporto => 1 (buon momento per BUY), se vicino alla resistenza => 0 (rischio SELL)
        df['support_resistance_score'] = 1 - (df['close'] - support) / range_val

    return df
