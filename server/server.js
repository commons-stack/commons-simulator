const express    = require('express')
const app = express()
const { exec } = require('child_process')
const bodyParser = require('body-parser')
const cors = require('cors')
const fs = require('fs')
const { Store } = require("fs-json-store");
const moment = require('moment')
const stringHash = require("string-hash");

// Creating data cache directory for the current deployment
const upTime = new Date().toISOString()
const DATA_DIR = `./data/${upTime}`
fs.mkdirSync(DATA_DIR)

app.use(cors())
app.use(bodyParser.json())

const server = app.listen(5000)

server.setTimeout(180000) // 3min

app.post('/cadcad', function(req, res) {
    console.log('/cadcad', req.body)
    let SIMULATION_COMMAND = `python3 ../simulation/simrunner.py `;
    try {
        [
            'hatchers',
            'proposals',
            'hatch_tribute',
            'vesting_80p_unlocked',
            'exit_tribute',
            'kappa',
            'days_to_80p_of_max_voting_weight',
            'max_proposal_request',
            'timesteps_days',
            'random_seed'
        ].forEach(arg => {
            if (!req.body[arg]) {
                throw new Error('missing parameter : ' + arg)
            }
            return SIMULATION_COMMAND += '--' + arg + ' ' + req.body[arg] + ' '
        })
    } catch (e) {
        return res.status(400).send(e.message)
    }

    const simulationId = stringHash(SIMULATION_COMMAND)
    const cacheFile = `${DATA_DIR}/${simulationId}.json`
    if (!fs.existsSync(cacheFile)) {
        console.log(SIMULATION_COMMAND + ' PROCESSING')
        const startTime = moment()
        exec(SIMULATION_COMMAND, (error, stdout, stderr) => {
            console.log(req.body, stdout, error, stderr)
            const endTime = moment()
            var timeDiff = endTime.diff(startTime, 'seconds')
            console.log('Total execution time (sec): ', timeDiff)
            if (error) return res.status(500).send(stderr)
            try {
                const lines = stdout.split(/\n/).filter(n => n)
                const json_output = JSON.parse(lines[lines.length - 1])
                const store = new Store({file: cacheFile})
                store.write([req.body, json_output, { execTimeinSec: timeDiff }])
                res.json(json_output)
            } catch (e) {
                if (e) res.status(500).send(stdout)
            }

        })
    } else {
        console.log(SIMULATION_COMMAND + ' CACHED')
        const store = new Store({file: cacheFile})
        store.read().then((data) => res.json(data[1]))
    }
});
