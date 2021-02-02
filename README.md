# Commons Simulator
![Commons Simulator](images/commons_simulator.png)
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
After running the simulation, the results will be shown in the CLI as a dictionary:

### Testing
From the main folder:
``` sh
python -m unittest discover -s simulation -p '*_test.py'
```


## Docker instructions

To run in a docker container

```sh
docker build -t commonssim .
docker run -p 5000:5000 commonssim
```

Go to http://localhost:5000/
