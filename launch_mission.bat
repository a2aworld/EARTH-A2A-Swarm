@echo off
title E.A.R.T.H. Mission Control
echo Initializing A2A World Environment...
python -m pip install pandas google-genai fastapi uvicorn requests streamlit
python D:\A2A_WORLD\mint_official_cards.py
streamlit run orchestrator.py
pause