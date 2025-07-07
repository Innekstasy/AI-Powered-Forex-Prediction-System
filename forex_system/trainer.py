import pandas as pd
import os
import joblib
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder

DATA_DIR = os.path.join("data")
MODEL_DIR = os.path.join("model")

def train_model_for_pair(pair, indicators_df):
    print(" Analisi del DataFrame prima del training:")
    print(f"Righe totali: {len(indicators_df)}")
    #print("Colonne con valori NaN:")
    #print(indicators_df.isna().sum())

    # Rimuovi le colonne non necessarie per il training
    columns_to_drop = [col for col in indicators_df.columns if any(x in col for x in ['timestamp', 'ML_TP', 'ML_SL'])]
    # features_df = indicators_df.drop(columns=columns_to_drop)

    score_cols = ['RSI_score', 'SMA_score', 'Fibonacci_score', 'support_resistance_score', 'wyckoff_score', 'ML_CONFIDENCE_SCORE']
    available_scores = [col for col in score_cols if col in indicators_df.columns and not indicators_df[col].isnull().all() and not (indicators_df[col] == 0).all()]

    if not available_scores:
        raise ValueError(f"❌ Nessun indicatore valido per il training per la coppia {pair}. Tutti i punteggi risultano nulli o mancanti.")

    features_df = indicators_df[available_scores + ['close', 'open', 'high', 'low', 'volume']].copy()

    # Encode categorical columns
    label_encoders = {}
    categorical_columns = features_df.select_dtypes(include=['object']).columns
    for col in categorical_columns:
        label_encoders[col] = LabelEncoder()
        features_df[col] = label_encoders[col].fit_transform(features_df[col].astype(str))

    # Sostituisci i NaN con valori appropriati per ogni colonna
    numeric_columns = features_df.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_columns:
        if 'close' in col.lower() or 'open' in col.lower() or 'high' in col.lower() or 'low' in col.lower():
            features_df.loc[:, col] = features_df[col].ffill().bfill()
        else:
            features_df.loc[:, col] = features_df[col].fillna(features_df[col].mean()).fillna(0)

    # Creazione target basata su movimento futuro (orizzonte di N candele)
    N = 15  # numero di candele da guardare avanti
    future_close = features_df['close'].shift(-N)

    tp_threshold = features_df['close'] * 0.001  # ad esempio, 0.05% sopra (≈ 5 pip)
    sl_threshold = features_df['close'] * 0.0015

    # TP prima di SL → 1, altrimenti 0
    price_change = future_close - features_df['close']
    target = (price_change > tp_threshold).astype(int)
    print("\n Distribuzione target (0 = SELL / 1 = BUY):")
    print(target.value_counts(normalize=True).round(4))

    # Rimuovi righe con NaN nel futuro
    # mask_valid = price_change.abs() > (tp_threshold / 10)
    mask_valid = ~price_change.isna()  # accetta tutte le righe con dati futuri
    features_df = features_df[mask_valid]
    print(" Righe eliminate per movimento prezzo troppo piccolo:", len(indicators_df) - len(features_df))
    target = target[mask_valid]

    print(f"\n Dopo la pulizia dei dati:")
    print(f"Righe rimanenti: {len(features_df)}")
    
    if len(features_df) < 10:
        raise ValueError(f" Dati insufficienti per il training ({len(features_df)} righe) per la coppia {pair}.")

    # Training
    X_train, X_test, y_train, y_test = train_test_split(features_df, target, test_size=0.2, shuffle=False)

    # Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Training XGBoost
    # 🚨 Bilanciamento opzionale: attivare se il modello predice solo SELL per troppo tempo
    use_balancing = True  # cambia a True se vuoi abilitare il bilanciamento automatico classi

    if use_balancing:
        # Calcola il bilanciamento pesato: esempi negativi / esempi positivi
        scale_pos_weight = (len(y_train) - sum(y_train)) / max(sum(y_train), 1)
        print(f" Bilanciamento attivo: scale_pos_weight = {scale_pos_weight:.2f}")
        model = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            scale_pos_weight=scale_pos_weight
        )
    else:
        # Nessun bilanciamento: comportamento standard
        model = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )

    model.fit(X_train_scaled, y_train)

    # Assicurati che la directory MODEL_DIR esista
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Salvataggio modello, scaler e colonne
    model_path = os.path.join(MODEL_DIR, f"model_{pair}.pkl")
    scaler_path = os.path.join(MODEL_DIR, f"scaler_{pair}.pkl")
    columns_path = os.path.join(MODEL_DIR, f"columns_{pair}.pkl")
    encoders_path = os.path.join(MODEL_DIR, f"encoders_{pair}.pkl")

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(features_df.columns.tolist(), columns_path)
    joblib.dump(label_encoders, encoders_path)  # Save the label encoders

    print(f" Modello salvato: {model_path}")
    print(f" Scaler salvato: {scaler_path}")
    print(f" Colonne salvate: {columns_path}")
    print(f" Label encoders salvati: {encoders_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        raise ValueError(" Devi specificare una coppia (es: EURUSD)")
    
    pair = sys.argv[1].upper()
    indicators_csv = os.path.join(DATA_DIR, f"indicators_{pair}.csv")

    if not os.path.exists(indicators_csv):
        raise FileNotFoundError(f" File non trovato: {indicators_csv}")
    
    indicators_df = pd.read_csv(indicators_csv)
    train_model_for_pair(pair, indicators_df)
