#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
echo "Configurez GOOGLE_API_KEY dans .env ou l'environnement, puis relancez si nécessaire."
streamlit run app.py
