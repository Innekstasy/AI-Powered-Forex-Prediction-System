# 🧠 AI-Powered Forex Prediction System

A fully open-source, modular, and offline-capable **Forex prediction system** built with the help of ChatGPT.  
It combines real-time data, technical indicators, and machine learning to generate BUY/SELL decisions and dynamically calculated Take Profit (TP) and Stop Loss (SL) targets.

> _"This won’t make you rich overnight, but it might help you make smarter decisions – and maybe a little extra money."_  

---

## 🚀 Why This Project?

I’m not a professional coder. I built this system **with ChatGPT**, driven by a desire to learn, explore, and automate logic-based trading without emotional interference.  
There are no subscriptions, no paid access, no hidden tools – just code, logic, and community.

> **I believe in open abundance, not closed systems.**

---

## 🧩 Features

- ✅ Fetches real-time data from multiple APIs (Yahoo, AlphaVantage, Polygon, etc.)
- ✅ Applies multiple technical indicators: RSI, SMA, ATR, Fibonacci, Support/Resistance, Wyckoff, Candlestick
- ✅ Trains a per-pair AI model (VotingClassifier)
- ✅ Predicts BUY/SELL actions and TP/SL levels with confidence scoring
- ✅ Logs predictions and compares with actual outcomes
- ✅ Generates daily performance reports (HTML format)
- ✅ Works **fully offline** after setup
- ✅ Modular and customizable architecture
- ✅ Includes test and utility scripts for validation and debugging

---

## 🧠 Tech Stack

- Python 3.10+
- Pandas, Scikit-Learn, XGBoost
- Jinja2 (for report generation)
- CMD (Windows Command Prompt)
- BAT file for launching essential scripts

---


## 📄 API Keys

Before running the system, make sure to configure your API keys in a `.env` file located in the `/srv` folder.

You can obtain these API keys **for free** by registering on the official websites of each provider. The source of each key is easily identified by the name:

```dotenv
ALPHAVANTAGE_API_KEY=your_key          # from alphavantage.co
POLYGON_API_KEY=your_key               # from polygon.io
TWELVEDATA_API_KEY=your_key            # from twelvedata.com
TRADERMADE_API_KEY=your_key            # from tradermade.com
EXCHANGERATES_API_KEY=your_key         # from exchangeratesapi.io
CURRENCYLAYER_API_KEY=your_key         # from currencylayer.com

You can leave out any unused keys — the system will automatically skip unavailable or over-limit APIs using a fallback mechanism.
🖥️ Windows Execution (via CMD)

The system is designed to run under Windows CMD.

To simplify the execution of all critical components, a SYSTEM.bat file is included. This script automatically launches the essential scripts in the correct order and environment.

    Just double-click SYSTEM.bat to start the system without using the terminal manually.

🧾 File Structure

The file STRUTTURA.txt provides a complete breakdown of the entire directory, including:

    Where each file is located

    What each script does

    Which folders contain models, logs, data, and configurations

This helps newcomers quickly navigate the system and understand its modularity.
📦 System Architecture

choose_currency_pair.py     # Select pair (e.g. EURUSD)
    ↓
update_and_train.py
    ├─ fetch_all_data.py     → fetch data from APIs
    ├─ merge_data.py         → clean & normalize data
    └─ trainer.py            → train ML model for the pair
    ↓
main.py
    ├─ final_decision.py     → make trade prediction
    └─ target_calculator.py  → determine TP/SL
    ↓
market_prediction_*.csv + result_*.csv logs
    ↓
evaluate_ai.py              → generate HTML performance report

📁 Project Organization

data/             → All market data files (raw, merged, indicator-based)
model/            → Trained models and preprocessors
log/              → Logs of predictions and performance evaluations
forex_system/     → Core logic and processing scripts
  ├─ fetch/       → Data fetching (API modules)
  ├─ indicators/  → Technical indicators and decision logic
srv/              → API keys and system config files
SYSTEM.bat        → Shortcut to run everything under CMD
STRUTTURA.txt     → Explains what each file and folder does

🧪 Test & Utility Scripts

The repo includes several helper scripts used for testing and maintenance:
Script	Purpose
test_fetch.py	Test API responses and latency
test_yahoo.py	Validate Yahoo Finance fetcher
check_csv.py	Integrity check on generated CSVs
clean_pending.py	Clean up corrupted or stuck signals
update_single_pair.py	Update one pair manually
🔧 Setup Instructions

Create virtual environment

python -m venv venv
venv\Scripts\activate

Install dependencies

pip install -r requirements.txt

Configure your .env with API keys (see above)

Run the system

    SYSTEM.bat

🤝 How to Contribute

    Refactor code or improve performance

    Suggest and implement new indicators

    Add backtesting or web UI

    Help translate into notebooks for beginners

Open a pull request or issue anytime.
⚠️ Disclaimer

This system is for educational and experimental use only.
It is not financial advice. Use it at your own risk.
📬 Final Words

Built with passion, curiosity, and the belief that knowledge should be shared freely.

    If this helps someone learn, save time, or gain confidence – it’s already a success.

📄 License

MIT License – use it, fork it, break it, improve it.
