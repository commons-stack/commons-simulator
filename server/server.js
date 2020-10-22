const express    = require('express')
const app = express()
const { exec } = require('child_process')
const bodyParser = require('body-parser')
const cors = require('cors')

app.use(cors())
app.use(bodyParser.json())

app.listen(5000)

let CACHE = {}

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
            'max_proposal_request'
        ].forEach(arg => {
            if (!req.body[arg]) {
                throw new Error('missing parameter : ' + arg)
            }
            return SIMULATION_COMMAND += '--' + arg + ' ' + req.body[arg] + ' '
        })
    } catch (e) {
        return res.status(400).send(e.message)
    }

    if (!CACHE[SIMULATION_COMMAND]) {
        console.log(SIMULATION_COMMAND + ' PROCESSING')
        exec(SIMULATION_COMMAND, (error, stdout, stderr) => {
            console.log(req.body, stdout, error, stderr)
            if (error) return res.status(500).send(stderr)
            try {
                const lines = stdout.split(/\n/).filter(n => n)
                const json_output = JSON.parse(lines[lines.length - 1])
                CACHE[SIMULATION_COMMAND] = json_output
                res.json(json_output)
            } catch (e) {
                if (e) res.status(500).send(stdout)
            }

        })
    } else {
        console.log(SIMULATION_COMMAND + ' CACHED')
        res.json(CACHE[SIMULATION_COMMAND])
    }
});
