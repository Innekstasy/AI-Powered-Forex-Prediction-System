
# Documentazione Interna - Sistema di Predizione AI Forex

## ✅ Flusso logico della predizione nel sistema

### 1. `loader.py`
- **Funzione principale**: prepara i dati da passare al modello.
- **Cosa fa**:
  - Applica tutti gli **indicatori tecnici** (`RSI`, `SMA`, `ATR`, `support_resistance`, ecc.) al dataset.
  - Aggiunge anche l’**indicatore personalizzato Fibonacci**.
  - **Restituisce**: un `DataFrame` pronto per il modello AI.

---

### 2. `ml.py`
- **Funzione chiave**: `predict_tp_sl_ml(df, pair)`
- **Cosa fa**:
  - Carica il modello AI (`VotingRegressor`) tramite `model_utils.load_model(pair)`.
  - Passa al modello l’ultima riga del `DataFrame` generato da `loader.py`.
  - Ottiene una **predizione di TP e SL**.
  - **Restituisce**: dizionario con `tp` e `sl` previsti.

---

### 3. `target_calculator.py`
- **Funzione chiave**: `calculate_reliability(tp, sl, last_close, trend)`
- **Cosa fa**:
  - Calcola un **indice di affidabilità (confidence score)** delle previsioni TP e SL in base al trend rilevato.
  - Lavora con la logica dei pips per misurare quanto TP e SL siano coerenti con il trend attuale.

- **Altra funzione chiave**: `weighted_mean(...)`
  - Combina TP/SL provenienti da **più metodi** (ML, Fibonacci, ecc.) usando pesi e affidabilità.

- **Restituisce**: valori TP/SL aggregati, normalizzati e ponderati.

---

### 4. `final_decision.py`
- **Funzione principale**: prende le decisioni operative.
- **Cosa fa**:
  - Riceve il `DataFrame` processato da `loader.py`.
  - Chiama:
    - `calculate_ml_indicator()` da `ml.py`
    - `calculate_reliability()` da `target_calculator.py`
    - `weighted_mean()` da `target_calculator.py`
  - Valuta i vari TP/SL da **modello AI, Fibonacci e altri indicatori**.
  - Sceglie il TP/SL finale da usare, in base a media ponderata e soglia minima di affidabilità.

- **Restituisce**:
  - `decision` (BUY/SELL/NONE)
  - `confidence`
  - `tp`, `sl` finali
  - `method_used` (AI, Fibonacci, ecc.)
  - commenti utili per log/report

---

## 🔁 Chi chiama chi

| Script              | Chiama                                         | Scopo principale |
|---------------------|------------------------------------------------|------------------|
| `main.py`           | `loader.py`, `final_decision.py`, `ml.py`     | esecuzione operativa |
| `loader.py`         | `rsi.py`, `sma_atr.py`, `support_resistance.py`, `fibonacci.py` | genera DataFrame con indicatori |
| `final_decision.py` | `ml.py`, `target_calculator.py`               | aggrega le decisioni |
| `ml.py`             | `model_utils.py`                              | fa le predizioni AI |
| `target_calculator.py` | -                                         | calcola affidabilità, fa media pesata |
| `fibonacci.py`      | -                                              | calcola livelli di Fibonacci e li normalizza |
| `model_utils.py`    | -                                              | carica modelli `.pkl` |

---

## ❓Fibonacci viene usato?
**Sì**:
- Viene **caricato da `loader.py`**
- È **valutato in `final_decision.py`**
- È **integrato nella media TP/SL** se produce valori utili.
