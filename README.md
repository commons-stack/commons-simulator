# Commons Simulator
![Commons Simulator](images/commons_simulator.png)

The Commons Simulator is a community project funded entirely by Gitcoin Grants, and undertaken by the Commons Stack’s dDev team. The Commons Simulator blends art and simulation into a dystopian sci-fi future where you travel back in time with cadCAD, a complex systems simulator that can predict the future.

![](https://miro.medium.com/max/1400/0*eNAd_BMZMMJ1VL-U)

You use cadCAD to help the fledgling RadicalxChange movement to customize their Cyber-Physical Commons to suit the needs of their community and save the world from ecosystem collapse!

## Server status

[![commons-stack](https://circleci.com/gh/commons-stack/commons-simulator.svg?style=svg)](https://app.circleci.com/pipelines/github/commons-stack/commons-simulator)


## 1. Installation:

```sh
sudo apt install nodejs npm
sudo npm install -g yarn
sudo pip3 install -r requirements.txt
./start.sh
```

## 2. Running the simulation:

### Running the simulation on CLI
To run the simulation on the CLI with the
default parameters:

```sh
cd simulation
python simrunner.py
```

Adding a `-h` shows all the possible input parameters:

``` sh
python simrunner.py -h
usage: simrunner.py [-h] [--hatchers HATCHERS] [--proposals PROPOSALS]
                    [--hatch_tribute HATCH_TRIBUTE]
                    [--vesting_80p_unlocked VESTING_80P_UNLOCKED]
                    [--exit_tribute EXIT_TRIBUTE] [--kappa KAPPA]
                    [--days_to_80p_of_max_voting_weight DAYS_TO_80P_OF_MAX_VOTING_WEIGHT]
                    [--max_proposal_request MAX_PROPOSAL_REQUEST]
                    [-T TIMESTEPS_DAYS] [--random_seed RANDOM_SEED]

optional arguments:
  -h, --help            show this help message and exit
  --hatchers HATCHERS
  --proposals PROPOSALS
  --hatch_tribute HATCH_TRIBUTE
  --vesting_80p_unlocked VESTING_80P_UNLOCKED
  --exit_tribute EXIT_TRIBUTE
  --kappa KAPPA
  --days_to_80p_of_max_voting_weight DAYS_TO_80P_OF_MAX_VOTING_WEIGHT
  --max_proposal_request MAX_PROPOSAL_REQUEST
  -T TIMESTEPS_DAYS, --timesteps_days TIMESTEPS_DAYS

```
After running the simulation, the results will be shown in the CLI as a dictionary.

### Development mode

To run a development mode server to have React hot reloading, do the same as above and in another terminal:
```sh
cd app
yarn start
```

A hot reloading server will pop up a browser tab on http://localhost:3000/

### Docker instructions

To run in a docker container

```sh
docker build -t commonssim .
docker run -p 5000:5000 commonssim
```

Go to http://localhost:5000/

### Website Front-End

The website Front-End repository can be found [here](https://github.com/commons-stack/c-sim-front-end).

## 3. Testing
From the main folder:
``` sh
python -m unittest discover -s simulation -p '*_test.py'
```

## 4. Resources

- [Play the game here!](https://sim.commonsstack.org/)
- [Medium Post](https://medium.com/commonsstack/the-commons-simulator-game-is-live-e1986615a105)
- [Gitcoin Grant](https://gitcoin.co/grants/277/commons-simulator-modeling-sustainable-funding-for)
- [Telegram Channel](https://t.me/CSDdev)
- [About the Commons Stack](https://commonsstack.org/)
