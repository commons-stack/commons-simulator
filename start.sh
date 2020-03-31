#!/bin/sh
set -o nounset

cd app
yarn
yarn build
cd ..
cp -r app/build/* static
source ./.envrc
gunicorn --bind 0.0.0.0:$PORT server:app
