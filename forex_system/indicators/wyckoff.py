import numpy as np

def calculate_wyckoff_phases(df):
    """
    Indicatore Wyckoff migliorato per identificare le fasi di accumulazione, markup, distribuzione e markdown.
    Restituisce la colonna 'wyckoff_phase' con valori: 'accumulation', 'markup', 'distribution', 'markdown', 'neutral'.
    """
    if df.empty or not {'close', 'volume'}.issubset(df.columns):
        df['wyckoff_phase'] = 'neutral'
        return df

    df = df.copy()

    window = 20
    df['price_change'] = df['close'].pct_change()
    df['volume_change'] = df['volume'].pct_change()
    df['rolling_close_std'] = df['close'].rolling(window).std()
    df['rolling_volume'] = df['volume'].rolling(window).mean()
    df['trend'] = df['close'].rolling(window).mean().diff()

    # Condizioni migliorate
    conditions = [
        # Accumulazione: volumi alti + trend neutro/debole + prezzo stabile
        (df['volume'] > df['rolling_volume'] * 1.1) &
        (df['price_change'].abs() < (df['rolling_close_std'] / df['close']) * 1.5) &
        (df['trend'].abs() < df['rolling_close_std'] * 0.2),

        # Markup: prezzo e trend in aumento + volumi crescenti
        (df['price_change'] > 0.001) &
        (df['trend'] > 0) &
        (df['volume_change'] > 0),

        # Distribuzione: volumi alti + trend piatto + prezzo elevato
        (df['volume'] > df['rolling_volume'] * 1.1) &
        (df['price_change'].abs() < (df['rolling_close_std'] / df['close']) * 1.5) &
        (df['trend'].abs() < df['rolling_close_std'] * 0.2) &
        (df['close'] > df['close'].rolling(50).mean()),

        # Markdown: prezzo e trend in calo + volumi crescenti
        (df['price_change'] < -0.001) &
        (df['trend'] < 0) &
        (df['volume_change'] > 0)
    ]

    choices = ['accumulation', 'markup', 'distribution', 'markdown']
    df['wyckoff_phase'] = np.select(conditions, choices, default='neutral')

    # Debug (opzionale)
    # print(df[['close', 'volume', 'price_change', 'trend', 'wyckoff_phase']].tail(10))

    phase_score = {
        'accumulation': 0.25,
        'markup': 1.0,
        'distribution': 0.5,
        'markdown': 0.0,
        'neutral': 0.5
    }
    df['wyckoff_score'] = df['wyckoff_phase'].map(phase_score).fillna(0.5)

    return df
