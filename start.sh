#!/bin/sh
set -o nounset

yarn --cwd app
yarn --cwd app build
cp -r app/build/* static
source ./.envrc
gunicorn --bind 0.0.0.0:$PORT -w $WORKERS server:app
