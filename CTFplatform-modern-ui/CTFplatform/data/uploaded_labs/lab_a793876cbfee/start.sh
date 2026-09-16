#!/bin/bash
set -e

echo "[+] Starting TechCorp Lab 5 — The Suspicious Email"
echo "[+] Checking Docker..."
if ! command -v docker >/dev/null 2>&1; then
  echo "[!] Docker is not installed or not available."
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  docker compose up --build
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose up --build
else
  echo "[!] Docker Compose is not available."
  exit 1
fi
