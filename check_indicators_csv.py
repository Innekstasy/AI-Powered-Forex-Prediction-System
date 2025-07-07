# import pandas as pd

# df = pd.read_csv("data/indicators_EURUSD.csv")

# nan_report = df.isna().sum()
# print("Colonne con NaN:")
# print(nan_report[nan_report > 0])

# inf_report = ((df == float("inf")) | (df == float("-inf"))).sum()
# print("\nColonne con inf:")
# print(inf_report[inf_report > 0])

import pandas as pd
import os
import glob

DATA_PATH = "data"

# Cerca tutti i file che iniziano con "indicators_" e finiscono con ".csv"
pattern = os.path.join(DATA_PATH, "indicators_*.csv")
files = glob.glob(pattern)

if not files:
    print(" Nessun file trovato.")
else:
    for file in files:
        symbol = os.path.basename(file).replace("indicators_", "").replace(".csv", "")
        print(f"\n Controllo file: {file} (Coppia: {symbol})")

        try:
            df = pd.read_csv(file)

            nan_report = df.isna().sum()
            nan_cols = nan_report[nan_report > 0]
            if not nan_cols.empty:
                print(" Colonne con NaN:")
                print(nan_cols)
            else:
                print(" Nessun NaN rilevato.")

            inf_report = ((df == float("inf")) | (df == float("-inf"))).sum()
            inf_cols = inf_report[inf_report > 0]
            if not inf_cols.empty:
                print(" Colonne con inf:")
                print(inf_cols)
            else:
                print(" Nessun valore infinito rilevato.")

        except Exception as e:
            print(f" Errore nel file {file}: {e}")
