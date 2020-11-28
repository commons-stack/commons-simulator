import argparse
import json

import pandas as pd
from cadCAD.configuration import Experiment
from cadCAD.configuration.utils import config_sim
from cadCAD.engine import ExecutionContext, ExecutionMode, Executor
from cadCAD import configs

from typing import Tuple
import unittest
import networkx as nx
import numpy as np
from networkx.classes.reportviews import NodeDataView

from hatch import create_token_batches, TokenBatch, Commons, convert_80p_to_cliff_and_halflife
from entities import attrs
from policies import GenerateNewParticipant, GenerateNewProposal, GenerateNewFunding, ActiveProposals, ProposalFunding, ParticipantVoting, ParticipantSellsTokens, ParticipantBuysTokens, ParticipantExits
from network_utils import bootstrap_network, calc_avg_sentiment, get_participants
from utils import new_probability_func, new_exponential_func, new_gamma_func, new_random_number_func, new_choice_func
from simulation import (CommonsSimulationConfiguration, bootstrap_simulation,
                        partial_state_update_blocks)


def bootstrap_simulation(c: CommonsSimulationConfiguration):
    contributions = [c.random_number_func() * 10e5 for i in range(c.hatchers)]
    cliff_days, halflife_days = c.cliff_and_halflife()
    token_batches, initial_token_supply = create_token_batches(
        contributions, 0.1, cliff_days, halflife_days)

    commons = Commons(sum(contributions), initial_token_supply,
                      hatch_tribute=c.hatch_tribute, exit_tribute=c.exit_tribute, kappa=c.kappa)
    network = bootstrap_network(
        token_batches, c.proposals, commons._funding_pool, commons._token_supply, c.max_proposal_request,
        c.probability_func, c.random_number_func, c.gamma_func, c.exponential_func)

    initial_conditions = {
        "network": network,
        "commons": commons,
        "funding_pool": commons._funding_pool,
        "collateral_pool": commons._collateral_pool,
        "token_supply": commons._token_supply,
        "token_price": commons.token_price(),
        "policy_output": None,
        "sentiment": 0.5
    }

    simulation_parameters = {
        'T': range(c.timesteps_days),
        'N': 1,
        'M': {
            # "sentiment_decay": 0.01, #termed mu in the state update function
            # "min_proposal_age_days": 7, # minimum periods passed before a proposal can pass,
            # "sentiment_sensitivity": 0.75,
            # 'min_supp':50, #number of tokens that must be stake for a proposal to be a candidate
            "debug": True,
            "alpha_days_to_80p_of_max_voting_weight": c.alpha(),
            "max_proposal_request": c.max_proposal_request,
            "random_seed": c.random_seed,
            "probability_func": c.probability_func,
            "exponential_func": c.exponential_func,
            "gamma_func": c.gamma_func,
            "random_number_func": c.random_number_func,
            "choice_func": c.choice_func
        }
    }

    return initial_conditions, simulation_parameters, network

def run_simulation(c: CommonsSimulationConfiguration):
    initial_conditions, simulation_parameters, network = bootstrap_simulation(c)

    exp = Experiment()
    exp.append_configs(
        initial_state=initial_conditions,
        partial_state_update_blocks=partial_state_update_blocks,
        sim_configs=simulation_parameters
    )

    # Do not use multi_proc, breaks ipdb.set_trace()
    exec_mode = ExecutionMode()
    single_proc_context = ExecutionContext(exec_mode.local_mode)
    executor = Executor(single_proc_context, configs)

    raw_system_events, tensor_field, sessions = executor.execute()

    df = pd.DataFrame(raw_system_events)
    df_final = df[df.substep.eq(2)]

    result = {
        "timestep": list(df_final["timestep"]),
        "funding_pool": list(df_final["funding_pool"]),
        "token_price": list(df_final["token_price"]),
        "sentiment": list(df_final["sentiment"])
    }
    return result, df_final, network

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    c_default = CommonsSimulationConfiguration()
    parser.add_argument("--hatchers", type=int, default=c_default.hatchers)
    parser.add_argument("--proposals", type=int, default=c_default.proposals)
    parser.add_argument("--hatch_tribute", type=float,
                        default=c_default.hatch_tribute)
    parser.add_argument("--vesting_80p_unlocked", type=float,
                        default=c_default.vesting_80p_unlocked)
    parser.add_argument("--exit_tribute", type=float,
                        default=c_default.exit_tribute)
    parser.add_argument("--kappa", type=int, default=c_default.kappa)
    parser.add_argument("--days_to_80p_of_max_voting_weight",
                        type=int, default=c_default.days_to_80p_of_max_voting_weight)
    parser.add_argument("--max_proposal_request", type=float,
                        default=c_default.max_proposal_request)
    parser.add_argument("-T", "--timesteps_days", type=int,
                        default=c_default.timesteps_days)
    args = parser.parse_args()

    c = CommonsSimulationConfiguration(**vars(args))
    print("Running sim config", c)
    o, _, network = run_simulation(c)
    print(json.dumps(o))
    print(_)
    participants = get_participants(network)
    for i, participant in participants:
        print("token batch age", participant.holdings.age_days)
