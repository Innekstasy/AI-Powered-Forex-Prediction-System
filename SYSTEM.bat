@echo off
:: Imposta la directory di lavoro
cd /d E:\CODE\FOREX_V4

:: 1. Apri la prima finestra CMD e attiva l'ambiente venv, quindi esegui update_and_train.py
start /min cmd /k "venv\Scripts\activate && python update_and_train.py"

:: 2. Attendi che lo script update_and_train.py termini
echo Attendo il completamento dello script update_and_train.py...
timeout /t 20 > nul

:: 3. Apri una nuova finestra CMD, attiva venv e prepara il comando per main_loop.py
start /min cmd /k "venv\Scripts\activate && python main_loop.py"

:: 4. Attendi che lo script main_loop.py termini
echo Attendo il completamento dello script main_loop.py...
timeout /t 5 > nul

:: 5. Apri una nuova finestra CMD, attiva venv e prepara il comando per main.py (senza eseguirlo)
start cmd /k "venv\Scripts\activate && cd /d E:\CODE\FOREX_V4 && echo python main.py"

:: 6. Apri un'altra finestra CMD, attiva venv e prepara il comando per evaluate_ai.py (senza eseguirlo)
start cmd /k "venv\Scripts\activate && cd /d E:\CODE\FOREX_V4 && echo python evaluate_ai.py"

echo Tutte le finestre CMD sono state aperte.
pause
