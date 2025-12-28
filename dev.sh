#!/usr/bin/env bash

# Load environment variables
if [ -f .env.local ]; then
    echo "Loading .env.local"
    export $(grep -v '^#' .env.local | xargs)
elif [ -f .env ]; then
    echo "Loading .env"
    export $(grep -v '^#' .env | xargs)
fi

# Ensure emulator is running
docker-compose up -d datastore

echo "Esperando a que el emulador de Datastore esté listo..."
sleep 5

# Run the app
uv run src/main.py
