#!/usr/bin/env bash
# Resets the TechCorp Information Disclosure lab to its original state.
# Only touches files inside this project's own database/ and documents/ dirs.
set -e

cd "$(dirname "$0")"

echo "== TechCorp Info-Disclosure Lab — Reset =="

if [ -d "venv" ]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
fi

echo "[*] Removing existing lab database (if any)..."
rm -f database/techcorp.db

echo "[*] Recreating users, initial data, and the document store..."
python3 -c "from app import init_db, init_docs; init_db(); init_docs()"

echo "[*] Lab reset complete. Restart the app with ./start.sh"
