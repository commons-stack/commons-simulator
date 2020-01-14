#!/bin/sh
cd app
yarn
yarn build
cd ..
cp -r app/build/* static
env FLASK_APP=server.py flask run
