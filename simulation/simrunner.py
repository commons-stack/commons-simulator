#!/usr/bin/env python
# coding: utf-8

from simulation import bootstrap_simulation, partial_state_update_blocks
import json
import argparse
import networkx as nx
import numpy as np
import pandas as pd
import datetime
from hatch import create_token_batches, TokenBatch, Commons
from convictionvoting import trigger_threshold
from policies import *
from network_utils import *
from entities import Participant, Proposal
from cadCAD.configuration import Configuration
from cadCAD.engine import ExecutionMode, ExecutionContext, Executor


def run_simulation(hatchers, proposals, hatch_tribute, vesting_80p_unlocked, exit_tribute, kappa, days_to_80p_of_max_voting_weight, proposal_max_size):
    # For the Flask backend

    # Commons/Augmented Bonding Curve parameters
    hatchers = 6
    proposals = 2
    hatch_tribute = 0.2
    vesting_80p_unlocked = 60
    exit_tribute = 0.35
    # kappa = 2, default option set in abcurve.py, there is no way to reach it from here for now

    # Conviction Voting parameters
    # used in ProposalFunding.su_calculate_gathered_conviction
    days_to_80p_of_max_voting_weight = 10
    max_proposal_request = 0.2  # will be passed to trigger_threshold()

    initial_conditions, simulation_parameters = bootstrap_simulation(
        hatchers, proposals, hatch_tribute, vesting_80p_unlocked, exit_tribute, 2, days_to_80p_of_max_voting_weight, max_proposal_request)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # The configurations above are then packaged into a `Configuration` object
    config = Configuration(initial_state=initial_conditions,  # dict containing variable names and initial values
                           # dict containing state update functions
                           partial_state_update_blocks=partial_state_update_blocks,
                           sim_config=simulation_parameters  # dict containing simulation parameters
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
parser.add_argument("hatchers")
parser.add_argument("proposals")
parser.add_argument("hatch_tribute")
parser.add_argument("vesting_80p_unlocked")
parser.add_argument("exit_tribute")
parser.add_argument("kappa")
parser.add_argument("days_to_80p_of_max_voting_weight")
parser.add_argument("proposal_max_size")
args = parser.parse_args()

o = run_simulation(args.hatchers, args.proposals, args.hatch_tribute, args.vesting_80p_unlocked,
                   args.exit_tribute, args.kappa, args.days_to_80p_of_max_voting_weight, args.proposal_max_size)
print(json.dumps(o))
