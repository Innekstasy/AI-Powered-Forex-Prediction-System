CURRENCY_PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD"
]


def choose_currency_pair():
    print("Seleziona una coppia di valute da analizzare:")
    for idx, pair in enumerate(CURRENCY_PAIRS, 1):
        print(f"{idx}. {pair}")
    print("6. Inserisci manualmente una coppia di valute")

    choice = input("Inserisci il numero della coppia da analizzare: ")

    if choice == "6":
        return input("Inserisci la coppia nel formato es: EUR/USD: ").upper()

    try:
        return CURRENCY_PAIRS[int(choice) - 1]
    except Exception:
        print("Scelta non valida. Uso EUR/USD di default.")
        return "EUR/USD"
 
