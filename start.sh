#!/bin/sh
cd app
yarn
yarn build
cd ..
cp -r app/build/* static
source ./.envrc
env FLASK_APP=server.py flask run
