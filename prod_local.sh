#!/usr/bin/env bash

# Cargar variables de entorno (TOKEN de Telegram, etc.)
if [ -f .env.local ]; then
    export $(grep -v '^#' .env.local | xargs)
elif [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# ASEGURAR que no vamos al emulador
unset DATASTORE_EMULATOR_HOST

echo "🚀 Iniciando cunhaobot contra DATOS DE PRODUCCIÓN..."
uv run uvicorn main:app --reload --host 0.0.0.0 --port 5050 --app-dir src
