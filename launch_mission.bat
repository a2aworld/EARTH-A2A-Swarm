@echo off
title E.A.R.T.H. Mission Control
echo Initializing A2A World Environment...

:: 1. Ensure all systems are installed
python -m pip install -r requirements.txt

:: 2. Mint the Official A2A Agent Cards (The Identity Layer)
echo.
echo 🛰️ Minting Official A2A Agent Cards...
python mint_official_cards.py

:: 3. Run the Vector Forge (Build the God-Brain)
echo.
echo 🧠 Building the God-Brain...
python build_vector_db.py

:: 4. Launch the Command Deck
echo.
echo 🌍 Launching E.A.R.T.H. Orchestrator...
streamlit run orchestrator.py

pause
