@echo off
title E.A.R.T.H. Mission Control
echo Initializing A2A World Environment...

:: 1. Ensure all systems are installed
python -m pip install pandas google-genai fastapi uvicorn requests streamlit

:: 2. Mint the Official A2A Agent Cards (The Identity Layer)
echo.
echo 🛰️ Minting Official A2A Agent Cards...
python D:\A2A_WORLD\mint_official_cards.py

:: 3. Launch the Command Deck
echo.
echo 🌍 Launching E.A.R.T.H. Orchestrator...
streamlit run orchestrator.py

pause
