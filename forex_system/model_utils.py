import os
import joblib

MODEL_DIR = os.path.join("model")

def load_model(pair):
    model_path = os.path.join(MODEL_DIR, f"model_{pair}.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Modello non trovato: {model_path}")

    model = joblib.load(model_path)
    return model
