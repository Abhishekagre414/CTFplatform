#!/bin/bash
set -e

echo "[+] Resetting TechCorp Lab 5..."

if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    docker compose down --remove-orphans
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose down --remove-orphans
  fi
fi

echo "[+] Lab containers stopped. Start again with ./start.sh"
