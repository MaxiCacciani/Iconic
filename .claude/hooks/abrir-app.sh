#!/usr/bin/env bash
# SessionStart: deja la app corriendo en Docker y la abre en Chrome (localhost:8080).
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0
URL=http://localhost:8080

if ! curl -s -o /dev/null --max-time 2 "$URL"; then
  if [ ! -f backend/.env ]; then
    echo '{"systemMessage":"No se abrió la app: falta backend/.env (copiar de .env.example)."}'
    exit 0
  fi
  docker compose up -d >/dev/null 2>&1
  for _ in $(seq 1 90); do
    curl -s -o /dev/null --max-time 2 "$URL" && break
    sleep 2
  done
fi

open -a "Google Chrome" "$URL"
echo '{"systemMessage":"App abierta en Chrome: '"$URL"'"}'
