# Conviction Voting Demo

## Usage

```sh
sudo pip3 install -r requirements.txt
env FLASK_APP=server.py flask run
```

## Docker instructions

To run in a docker container

```sh
docker build -t cvdemo .
docker run -p 5000:5000 cvd
```

Go to http://localhost:5000/

