import pandas as pd
import glob
import os
import webbrowser
from datetime import datetime
from jinja2 import Template
import yfinance as yf
from datetime import timedelta

def is_pending_expired(timestamp, max_days=10):
    """Controlla se il segnale pending è scaduto (più vecchio di 10 giorni)"""
    try:
        trade_time = pd.to_datetime(timestamp)
        time_diff = datetime.now() - trade_time
        return time_diff > timedelta(days=max_days)
    except Exception as e:
        print(f" Errore nel controllo scadenza pending: {e}")
        return False

PREDICTIONS_LOG_DIR = os.path.join("log", "predictions")
INDICATORS_DIR = os.path.join("data")  # dove hai gli indicators_*.csv
REPORT_DIR = os.path.join("log", "evaluate_ai")
os.makedirs(REPORT_DIR, exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Valutazione AI Forex</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { padding: 10px; border: 1px solid #ccc; text-align: center; }
        th { background-color: #f4f4f4; }
        h2, h3 { background-color: #e8e8e8; padding: 10px; }
        .success { color: green; font-weight: bold; }
        .failure { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>📊 Valutazione AI Forex</h1>

    <h2>Risultati valutazione predizioni AI</h2>
    <table>
        <tr>
            <th>Azione</th>
            <th>Esito</th>
            <th>Precision</th>
            <th>Recall</th>
        </tr>
        {% for action, result in summary.items() %}
        <tr>
            <td>{{ action }}</td>
            <td>{{ result['esito'] }}</td>
            <td>{{ result['precision'] }}%</td>
            <td>{{ result['recall'] }}%</td>
        </tr>
        {% endfor %}
    </table>

    <h2>Rendimento operativo stimato</h2>
    <table>
        <tr>
            <th>Esito</th>
            <th>Conteggio</th>
            <th>Percentuale</th>
        </tr>
        {% for outcome, data in performance.items() %}
        <tr>
            <td>{{ outcome }}</td>
            <td>{{ data['count'] }}</td>
            <td>{{ data['percentage'] }}%</td>
        </tr>
        {% endfor %}
    </table>

    <h2>Riepilogo Operazioni</h2>
    <table>
        <tr>
            <th>Tipo</th>
            <th>Numero</th>
            <th>Percentuale</th>
        </tr>
        <tr>
            <td>Totale Operazioni</td>
            <td>{{ trades_summary.total }}</td>
            <td>100%</td>
        </tr>
        <tr>
            <td>Operazioni Chiuse</td>
            <td>{{ trades_summary.closed }}</td>
            <td>{{ (trades_summary.closed / trades_summary.total * 100)|round(2) }}%</td>
        </tr>
        <tr>
            <td>Operazioni in Attesa</td>
            <td>{{ trades_summary.pending }}</td>
            <td>{{ (trades_summary.pending / trades_summary.total * 100)|round(2) }}%</td>
        </tr>
        <tr>
            <td>Tasso di Successo (TP)</td>
            <td colspan="2">{{ trades_summary.success_rate|round(2) }}%</td>
        </tr>
    </table>

    <h2>Storico rendimento (ultimi 10 giorni)</h2>
    <table>
        <tr>
            <th>Data</th>
            <th>TP</th>
            <th>SL</th>
            <th>Precision</th>
        </tr>
        {% for day in history %}
        <tr>
            <td>{{ day['date'] }}</td>
            <td>{{ day['tp'] }}</td>
            <td>{{ day['sl'] }}</td>
            <td>{{ day['precision'] }}%</td>
        </tr>
        {% endfor %}
    </table>

    <h3>Legenda interpretazione indicatori</h3>
    <table>
    <tr><th>Interpretazione</th><th>Significato</th></tr>
    <tr><td>Bullish</td><td>Tendenza al rialzo</td></tr>
    <tr><td>Accumulation</td><td>Fase di accumulo (possibile inversione positiva)</td></tr>
    <tr><td>Lateral</td><td>Mercato in laterale / indeciso</td></tr>
    <tr><td>Distribution</td><td>Fase di distribuzione (possibile inversione negativa)</td></tr>
    <tr><td>Bearish</td><td>Tendenza al ribasso</td></tr>
    </table>

    <h2>Interpretazione degli Indicatori (ultimo aggiornamento)</h2>
    {% for pair, indicators in grouped_indicators.items() %}
        <h3>{{ pair }}</h3>
        <table>
            <tr>
                <th>Indicatore</th>
                <th>Valore</th>
                <th>Interpretazione</th>
            </tr>
            {% for ind in indicators %}
            <tr>
                <td>{{ ind.indicator }}</td>
                <td>{{ ind.value }}</td>
                <td>{{ ind.interpretation }}</td>
            </tr>
            {% endfor %}
        </table>
    {% endfor %}

    <h2>Segnali ancora in attesa</h2>
    <table>
        <tr>
            <th>Timestamp</th>
            <th>Symbol</th>
            <th>Azione</th>
            <th>TP</th>
            <th>SL</th>
            <th>Status</th>
        </tr>
        {% for signal in pending_signals %}
        <tr>
            <td>{{ signal['timestamp'] }}</td>
            <td>{{ signal['symbol'] }}</td>
            <td>{{ signal['action'] }}</td>
            <td>{{ signal['tp'] }}</td>
            <td>{{ signal['sl'] }}</td>
            <td>{{ signal['status'] }}</td>
        </tr>
        {% endfor %}
    </table>


</body>
</html>
"""

from scrape_xe import get_xe_price  # Importazione dello scraping XE

def get_current_price(pair, max_retries=3):
    """Ottiene il prezzo corrente, utilizzando Yahoo come primario e XE come fallback"""
    try:
        # Tentativo con Yahoo Finance (primaria)
        try:
            ticker = yf.Ticker(f"{pair}=X")
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                price = data['Close'].iloc[-1]
                return price
        except Exception as e:
            pass  # Silenziosamente passa al fallback

        # Fallback: Tentativo con XE.com
        price = get_xe_price(pair)
        if price:
            return price
        return None

    except Exception as e:
        print(f" Errore nel recupero prezzo per {pair}: {str(e)}")
        return None

def is_trade_closed(trade, current_price):
    """Verifica se una operazione è stata chiusa (TP o SL)"""
    if not current_price:
        return False
        
    if trade['action'] == 'BUY':
        if current_price >= float(trade['tp']):
            return True  # TP raggiunto
        if current_price <= float(trade['sl']):
            return True  # SL raggiunto
    else:  # SELL
        if current_price <= float(trade['tp']):
            return True  # TP raggiunto
        if current_price >= float(trade['sl']):
            return True  # SL raggiunto
    return False

def get_trade_outcome(trade, current_price):
    """Determina se l'operazione chiusa ha raggiunto TP o SL"""
    if trade['action'] == 'BUY':
        return 'TP' if current_price >= float(trade['tp']) else 'SL'
    else:  # SELL
        return 'TP' if current_price <= float(trade['tp']) else 'SL'

def validate_trade_outcome(trade, max_lookback_days=30):
    """Verifica il reale outcome del trade analizzando i dati storici"""
    try:
        trade_time = pd.to_datetime(trade['timestamp'])
        end_time = min(datetime.now(), trade_time + pd.Timedelta(days=max_lookback_days))
        
        symbol = f"{trade['pair']}=X"
        hist = yf.download(symbol, start=trade_time, end=end_time, interval='5m', progress=False)
        
        if hist.empty:
            return "DATI_MANCANTI"
            
        entry_price = float(trade['current_price'])
        tp = float(trade['tp'])
        sl = float(trade['sl'])
        
        for idx, row in hist.iterrows():
            high = float(row['High'].iloc[0]) if isinstance(row['High'], pd.Series) else float(row['High'])
            low = float(row['Low'].iloc[0]) if isinstance(row['Low'], pd.Series) else float(row['Low'])

            if trade['action'] == 'BUY':
                if high >= tp:
                    return "TP_REALE"
                if low <= sl:
                    return "SL_REALE"
            else:  # SELL
                if low <= tp:
                    return "TP_REALE"
                if high >= sl:
                    return "SL_REALE"
                    
        return trade['status']  # Mantiene lo status originale se non è stato raggiunto TP/SL
        
    except Exception as e:
        return f"ERRORE: {str(e)}"

def interpret_indicator(value):
    if value >= 0.75:
        return " Bullish"
    elif value >= 0.55:
        return " Accumulation"
    elif value >= 0.45:
        return " Lateral"
    elif value >= 0.25:
        return " Distribution"
    else:
        return " Bearish"

def generate_evaluation_report(open_browser=True):
    prediction_files = glob.glob(os.path.join(PREDICTIONS_LOG_DIR, "market_prediction_*.csv"))
    
    # Strutture dati per il tracking
    closed_trades = []
    pending_signals = []
    total_trades = 0
    
    # Initialize summary structures
    summary = {
        'BUY': {'esito': 0, 'precision': 0, 'recall': 0},
        'SELL': {'esito': 0, 'precision': 0, 'recall': 0}
    }
    
    performance = {
        'TP': {'count': 0, 'percentage': 0},
        'SL': {'count': 0, 'percentage': 0},
        'PENDING': {'count': 0, 'percentage': 0}
    }
    
    history = []  # Will be populated with daily performance data
    
    # Elaborazione dei file di predizione
    for file in prediction_files:
        df = pd.read_csv(file)
        file_pending_signals = []

        # Cattura i segnali IN ATTESA attuali per debug
        for _, trade in df.iterrows():
            status = str(trade.get('status', '')).strip().upper()
            if status == 'IN ATTESA':
                file_pending_signals.append({
                    'timestamp': trade.get('timestamp'),
                    'symbol': trade.get('symbol'),
                    'action': trade.get('action'),
                    'file': os.path.basename(file),
                    'status_raw': trade.get('status')
                })

        if file_pending_signals:
            # print(f"\n Segnali IN ATTESA trovati in: {os.path.basename(file)}")
            for signal in file_pending_signals:
                # print(f"    {signal['timestamp']} | {signal.get('symbol', '???')} | {signal.get('action', '???')} | status letto: {signal.get('status_raw', '???')}")
                pass

        total_trades += len(df)

        # Verifica se la colonna 'status' esiste, altrimenti la crea con valore 'IN ATTESA'
        if 'status' not in df.columns:
            # print(f" Colonna 'status' mancante nel file {file}. Inizializzazione con valore 'IN ATTESA'.")
            df['status'] = "IN ATTESA"
            df.to_csv(file, index=False)
        
        for _, trade in df.iterrows():
            # Assicurati che il symbol sia sempre presente
            # Recupera symbol da 'pair', da 'symbol', o dal nome file
            symbol = (
                trade.get('pair')
                or trade.get('symbol')
                or os.path.basename(file).split("_")[2].upper()
            )
            trade_copy = trade.copy()
            trade_copy['symbol'] = symbol
    
            # Forza lo status se assente
            if 'status' not in trade or pd.isna(trade['status']):
                trade_copy['status'] = 'IN ATTESA'

            # Scarta trade incompleti
            required_fields = ['action', 'tp', 'sl', 'timestamp']
            if not all(f in trade and pd.notna(trade[f]) for f in required_fields):
                # print(f" Segnale incompleto scartato in {os.path.basename(file)}: {trade}")
                continue

            current_price = get_current_price(symbol)
            if current_price and is_trade_closed(trade_copy, current_price):
                outcome = get_trade_outcome(trade_copy, current_price)
                trade_copy['status'] = outcome
                closed_trades.append(trade_copy)
                performance[outcome]['count'] += 1
            elif str(trade.get('status', '')).strip().upper() == "IN ATTESA":
                if is_pending_expired(trade['timestamp']):
                    trade_copy['status'] = "SCADUTO"
                    closed_trades.append(trade_copy)
                    performance['SL']['count'] += 1
                else:
                    trade_copy['status'] = "IN ATTESA"
                    pending_signals.append(trade_copy)
                    performance['PENDING']['count'] += 1
    
    # Calculate percentages
    total_results = len(closed_trades) + len(pending_signals)
    if total_results > 0:
        for key in performance:
            performance[key]['percentage'] = (performance[key]['count'] / total_results) * 100

    # Calculate success rates for summary with real precision
    for action in ['BUY', 'SELL']:
        action_trades = [t for t in closed_trades if t['action'] == action]
        pending_action = [t for t in pending_signals if t['action'] == action]
        
        if action_trades:
            # Count successful trades
            successful = len([t for t in action_trades if t['status'] == 'TP'])
            failed = len([t for t in action_trades if t['status'] == 'SL'])
            total_closed = len(action_trades)
            total_all = total_closed + len(pending_action)
            
            # Calculate real precision and recall
            precision = (successful / total_closed) * 100 if total_closed > 0 else 0
            recall = (successful / total_all) * 100 if total_all > 0 else 0
            
            # Update summary with real values
            summary[action].update({
                'esito': f"{successful}/{total_closed} ({failed} SL)",
                'precision': round(precision, 2),
                'recall': round(recall, 2)
            })
            
            # Debug logging
            print(f"\nAnalisi dettagliata {action}:")
            print(f"Trade chiusi: {total_closed}")
            print(f"Trade in attesa: {len(pending_action)}")
            print(f"TP raggiunti: {successful}")
            print(f"SL raggiunti: {failed}")
            print(f"Precision reale: {precision:.2f}%")
            print(f"Recall reale: {recall:.2f}%")
    
    # Calculate daily history (last 10 days) - Fixed version
    all_dates = []
    for file in prediction_files:
        df = pd.read_csv(file)
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        all_dates.extend(df['date'].unique())
    
    unique_dates = sorted(set(all_dates))[-10:]  # Get last 10 days
    
    for date in unique_dates:
        day_trades = [t for t in closed_trades if pd.to_datetime(t['timestamp']).date() == date]
        if day_trades:
            tp_count = len([t for t in day_trades if t['status'] == 'TP'])
            sl_count = len([t for t in day_trades if t['status'] == 'SL'])
            precision = (tp_count / len(day_trades)) * 100 if day_trades else 0
            history.append({
                'date': date.strftime('%Y-%m-%d'),
                'tp': tp_count,
                'sl': sl_count,
                'precision': precision
            })

    # Generate report
    trades_summary = {
        'total': total_trades,
        'closed': len(closed_trades),
        'pending': len(pending_signals),
        'success_rate': (len([t for t in closed_trades if t['status'] == 'TP']) / len(closed_trades) * 100) if closed_trades else 0
    }

    indicator_summary = []

    indicator_files = glob.glob(os.path.join(INDICATORS_DIR, "indicators_*.csv"))

    for file in indicator_files:
        try:
            df = pd.read_csv(file)
            if df.empty:
                continue
            latest_row = df.iloc[-1]
            indicators = [col for col in df.columns if col.endswith("_score")]

            for ind in indicators:
                val = latest_row.get(ind, None)
                if val is not None and pd.notna(val):
                    pair_name = os.path.basename(file).replace('indicators_', '').replace('.csv','').upper()
                    indicator_name = ind.replace('_score', '').upper()

                    indicator_summary.append({
                        "pair": pair_name,
                        "indicator": indicator_name,
                        "value": round(float(val), 3),
                        "interpretation": interpret_indicator(val)
                    })
        except Exception as e:
            print(f"Errore lettura indicatori da {file}: {e}")

    from collections import defaultdict

    grouped_indicators = defaultdict(list)
    for ind in indicator_summary:
        grouped_indicators[ind['pair']].append(ind)

    # Generazione del report HTML
    report_html = Template(HTML_TEMPLATE).render(
        summary=summary,
        performance=performance,
        history=history,
        pending_signals=pending_signals,
        trades_summary=trades_summary,
        closed_trades=closed_trades,
        # indicator_summary=indicator_summary
        grouped_indicators=grouped_indicators,
    )

    report_file = os.path.join(REPORT_DIR, f"valutazione_ai_{datetime.now().strftime('%Y%m%d%H%M%S')}.html")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_html)

    print(f"Report valutazione generato: {report_file}")

    # Apri il report nel browser solo se open_browser è True
    if open_browser:
        webbrowser.open(f"file://{os.path.abspath(report_file)}")

if __name__ == "__main__":
    generate_evaluation_report()
