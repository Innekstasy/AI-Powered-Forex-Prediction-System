import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join("srv", ".env"))

# Altre configurazioni
DEFAULT_INTERVAL = "1h"
DEFAULT_OUTPUT_SIZE = 500  # o il numero di barre da richiedere

# Percorso cartella srv
SRV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "srv")

# Alpha Vantage
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

# CurrencyLayer
CURRENCYLAYER_API_KEY = os.getenv("CURRENCYLAYER_API_KEY")
CURRENCYLAYER_URL = "http://apilayer.net/api/"

# ExchangeRates
EXCHANGERATES_API_KEY = os.getenv("EXCHANGERATES_API_KEY")
EXCHANGERATES_URL = "https://v6.exchangeratesapi.io/latest"

# Polygon
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
POLYGON_URL = "https://api.polygon.io"

# TraderMade
TRADERMADE_API_KEY = os.getenv("TRADERMADE_API_KEY")
TRADERMADE_URL = "https://api.tradermade.com"

# TwelveData
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY")
TWELVEDATA_URL = "https://api.twelvedata.com"

# Altre configurazioni
DEFAULT_INTERVAL = "1h"
DEFAULT_OUTPUT_SIZE = 500  # o il numero di barre da richiedere

# Percorso per i file di log
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log")

# Assicurati che la directory esista
os.makedirs(LOG_PATH, exist_ok=True)

# Percorso per i file di dati
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Assicurati che la directory esista
os.makedirs(DATA_PATH, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
