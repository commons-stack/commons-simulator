#!/usr/bin/env python
# coding: utf-8

from simulation import bootstrap_simulation, partial_state_update_blocks, CommonsSimulationConfiguration
import json
import argparse
import pandas as pd
from cadCAD.configuration import Configuration
from cadCAD.engine import ExecutionMode, ExecutionContext, Executor


def run_simulation(c: CommonsSimulationConfiguration):
    initial_conditions, simulation_parameters = bootstrap_simulation(c)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # The configurations above are then packaged into a `Configuration` object
    config = Configuration(initial_state=initial_conditions,
                           partial_state_update_blocks=partial_state_update_blocks,
                           sim_config=simulation_parameters
                           )

    exec_mode = ExecutionMode()
    # Do not use multi_proc, breaks ipdb.set_trace()
    exec_context = ExecutionContext(exec_mode.single_proc)
    # Pass the configuration object inside an array
    executor = Executor(exec_context, [config])
    # The `execute()` method returns a tuple; its first elements contains the raw results
    raw_result, tensor = executor.execute()

    # In[6]:

    df = pd.DataFrame(raw_result)
    df_final = df[df.substep.eq(2)]

    result = {
        "timestep": list(df_final["timestep"]),
        "funding_pool": list(df_final["funding_pool"]),
        "token_supply": list(df_final["token_supply"]),
        "collateral": list(df_final["collateral_pool"])
    }
    return result


parser = argparse.ArgumentParser()
parser.add_argument("hatchers", type=int)
parser.add_argument("proposals", type=int)
parser.add_argument("hatch_tribute", type=float)
parser.add_argument("vesting_80p_unlocked", type=float)
parser.add_argument("exit_tribute", type=float)
parser.add_argument("kappa", type=int)
parser.add_argument("days_to_80p_of_max_voting_weight", type=int)
parser.add_argument("proposal_max_size", type=float)
args = parser.parse_args()

c = CommonsSimulationConfiguration()
c.hatchers = args.hatchers
c.proposals = args.proposals
c.hatch_tribute = args.hatch_tribute
c.vesting_80p_unlocked, = args.vesting_80p_unlocked,
c.exit_tribute = args.exit_tribute
c.kappa = args.kappa
c.days_to_80p_of_max_voting_weight = args.days_to_80p_of_max_voting_weight
c.proposal_max_size = args.proposal_max_size

o = run_simulation(c)
print(json.dumps(o))
