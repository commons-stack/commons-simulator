# Commons Simulator

## Dependencies

```sh
sudo apt install nodejs npm
sudo npm install -g yarn
sudo pip3 install -r requirements.txt
```

## Environment

Set up the necessary environment variables by making a copy of `.envrc.example` to `.envrc` and filling in the necessary variables. Do not commit this file!

## Using Nix

Using Nix package manager:

1. Install Nix: `curl -L --proto '=https' --tlsv1.2 https://nixos.org/nix/install | sh`
2. Run `nix-shell` in root directory
3. Run `start`
4. Open `localhost:5000` in browser

## Usage

```sh
./start.sh
```

Then open `localhost:5000` in browser.

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

## Notes / issues

1. If you don't serve the app via Flask, cookie sessions will not work. I don't think this is an issue, as we can still use a CDN for all Javascript and image content, even if served via Flask.