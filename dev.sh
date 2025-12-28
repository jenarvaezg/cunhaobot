#!/usr/bin/env bash

# Load .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Ensure emulator is running
docker-compose up -d datastore

echo "Esperando a que el emulador de Datastore esté listo..."
sleep 5

# Run the app
uv run src/main.py
