# Commons Simulator Server

## Usage

```sh
sudo apt install nodejs npm
npm i
node server.js
```

## Production

```sh
npm i -g pm2
pm2 start server.js
```

## Monitoring server status

```sh
pm2 status
pm2 logs --format <pid>
```
