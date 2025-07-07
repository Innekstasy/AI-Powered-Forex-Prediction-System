from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

def get_xe_price(pair):
    """Recupera il prezzo live della coppia Forex da XE.com utilizzando Selenium"""
    try:
        # Formattazione della coppia (es: EURUSD -> EUR-USD)
        base, quote = pair[:3], pair[3:]
        url = f"https://www.xe.com/currencyconverter/convert/?Amount=1&From={base}&To={quote}"
        print(f"🌐 Recupero prezzo da: {url}")

        # Imposta il driver di Chrome (modalità headless per esecuzione silenziosa)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Modalità senza interfaccia grafica
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')  # Disabilita l'uso della GPU
        options.add_argument('--log-level=3')  # Riduce i messaggi di log

        driver = webdriver.Chrome(service=Service("E:/CODE/FOREX_V3/chrome-win64/chromedriver.exe"), options=options)
        driver.get(url)

        # Attendi il caricamento completo della pagina
        time.sleep(5)  # Attesa iniziale

        try:
            # Attendere fino a 30 secondi per la visibilità del prezzo usando un XPath generico
            price_tag = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.XPATH, "//p[contains(text(), '1 ')]"))
            )
            price_text = price_tag.text
            print(f"📊 Test Prezzo Estratto: {price_text}")

            # Usa una regex per estrarre il numero dopo "1 USD = "
            match = re.search(r"1 USD = ([\d\.]+) EUR", price_text)
            if match:
                # Invertire il rapporto per ottenere EUR/USD
                usd_to_eur = float(match.group(1))
                eur_to_usd = 1 / usd_to_eur
                print(f"✅ Prezzo ottenuto per {pair}: {eur_to_usd:.5f}")
                driver.quit()
                return eur_to_usd
            else:
                print("⚠️ Formato del prezzo non riconosciuto")
                driver.quit()
                return None
        except Exception as e:
            # Stampiamo l'intero contenuto della pagina per debug
            print("⚠️ Errore nel recupero del prezzo:", e)
            driver.quit()
            return None

    except Exception as e:
        print(f"❌ Errore durante lo scraping: {e}")
        return None

if __name__ == "__main__":
    while True:
        price = get_xe_price("EURUSD")
        if price:
            print(f"📈 Prezzo EUR/USD: {price:.5f}")
        else:
            print("⚠️ Nessun prezzo disponibile.")
        time.sleep(10)  # Intervallo tra le richieste
