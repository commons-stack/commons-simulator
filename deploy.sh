#!/bin/sh
set -o nounset

source .envrc
heroku container:push web \
    --arg SECRET_KEY=$SECRET_KEY
    --arg REACT_APP_SERVER_URI=$REACT_APP_SERVER_URI
heroku container:release web