#!/usr/bin/env bash

prev_version=$(gcloud app versions list | tail -n 1 | tr -s " " | cut -d' ' -f2)

echo y | gcloud app deploy --stop-previous-version
echo y | gcloud app versions delete $prev_version

curl https://cunhaobot.appspot.com
