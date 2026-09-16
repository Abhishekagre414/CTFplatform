#!/usr/bin/env bash
# Starts the TechCorp Information Disclosure training lab.
set -e

cd "$(dirname "$0")"

echo "== TechCorp Info-Disclosure Lab — Starting =="

if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv venv
fi

# shellcheck disable=SC1091
source venv/bin/activate

echo "[*] Installing/checking dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

if [ ! -f "database/techcorp.db" ]; then
    echo "[*] Initializing database..."
    python3 -c "from app import init_db; init_db()"
else
    echo "[*] Existing database found. Use ./reset.sh to restore a fresh lab state."
fi

echo "[*] Rebuilding fictional document store..."
python3 -c "from app import init_docs; init_docs()"

echo "[*] Starting Flask application on http://127.0.0.1:5000 ..."
python3 app.py
