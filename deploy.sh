#!/usr/bin/env bash

# Export requirements.txt using uv if available
if command -v uv &> /dev/null; then
    echo "Generating requirements.txt with uv..."
    uv export --no-hashes --format requirements-txt > requirements.txt
fi

prev_version=$(gcloud app versions list | tail -n 1 | tr -s " " | cut -d' ' -f2)

echo y | gcloud app deploy --stop-previous-version --promote --no-cache
echo y | gcloud app versions delete $prev_version

curl https://cunhaobot.appspot.com
