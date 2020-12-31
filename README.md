# Commons Simulator

## Server status

[![commons-stack](https://circleci.com/gh/commons-stack/commons-simulator.svg?style=svg)](https://app.circleci.com/pipelines/github/commons-stack/commons-simulator)

## Usage

```sh
sudo apt install nodejs npm
sudo npm install -g yarn
sudo pip3 install -r requirements.txt
./start.sh
```

### Development mode

To run a development mode server to have React hot reloading, do the same as above and in another terminal:
```sh
cd app
yarn start
```

A hot reloading server will pop up a browser tab on http://localhost:3000/

## Docker instructions

To run in a docker container

```sh
docker build -t commonssim .
docker run -p 5000:5000 commonssim
```

Go to http://localhost:5000/
