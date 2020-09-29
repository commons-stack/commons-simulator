#!/usr/bin/env python
# coding: utf-8

# In[1]:
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

    # In[3]:

    def update_collateral_pool(params, step, sL, s, _input):
        commons = s["commons"]
        s["collateral_pool"] = commons._collateral_pool
        return "collateral_pool", commons._collateral_pool

    def update_token_supply(params, step, sL, s, _input):
        commons = s["commons"]
        s["token_supply"] = commons._token_supply
        return "token_supply", commons._token_supply

    def update_funding_pool(params, step, sL, s, _input):
        commons = s["commons"]
        s["funding_pool"] = commons._funding_pool
        return "funding_pool", commons._funding_pool

    # In[4]:

    contributions = [np.random.rand() * 10e5 for i in range(hatchers)]
    token_batches, initial_token_supply = create_token_batches(
        contributions, 0.1, vesting_80p_unlocked)

    commons = Commons(sum(contributions), initial_token_supply,
                      hatch_tribute=0.2, exit_tribute=0.35)
    network = bootstrap_network(
        token_batches, proposals, commons._funding_pool, commons._token_supply, max_proposal_request)

    initial_conditions = {
        "network": network,
        "commons": commons,
        "funding_pool": commons._funding_pool,
        "collateral_pool": commons._collateral_pool,
        "token_supply": commons._token_supply,
        "sentiment": 0.5,
    }

    partial_state_update_blocks = [
        {
            "policies": {
                "generate_new_participants": GenerateNewParticipant.p_randomly,
            },
            'variables': {
                'network': GenerateNewParticipant.su_add_to_network,
                'commons': GenerateNewParticipant.su_add_investment_to_commons,
            }
        },
        {
            "policies": {},
            "variables": {
                "funding_pool": update_funding_pool,
                "collateral_pool": update_collateral_pool,
                "token_supply": update_token_supply,
            }
        },
        {
            "policies": {
                "generate_new_proposals": GenerateNewProposal.p_randomly,
            },
            "variables": {
                "network": GenerateNewProposal.su_add_to_network,
            }
        },
        {
            "policies": {
                "generate_new_funding": GenerateNewFunding.p_exit_tribute_of_average_speculator_position_size,
            },
            "variables": {
                "network": GenerateNewFunding.su_add_funding,
            }
        },
        {
            "policies": {},
            "variables": {
                "network": ProposalFunding.su_update_age_and_conviction_thresholds,
            }
        },
        {
            "policies": {
                "decide_which_proposals_should_be_funded": ProposalFunding.p_compare_conviction_and_threshold
            },
            "variables": {
                "network": ProposalFunding.su_compare_conviction_and_threshold_make_proposal_active,
                "commons": ProposalFunding.su_compare_conviction_and_threshold_deduct_funds_from_funding_pool,
            }
        },
        {
            "policies": {},
            "variables": {
                "funding_pool": update_funding_pool,
                "collateral_pool": update_collateral_pool,
                "token_supply": update_token_supply,
            }
        },
        {
            "policies": {
                "participants_stake_tokens_on_proposals": ParticipantVoting.p_participant_votes_on_proposal_according_to_affinity
            },
            "variables": {
                "network": ParticipantVoting.su_update_participants_votes,
            },
        },
        {
            "policies": {},
            "variables": {
                "network": ProposalFunding.su_calculate_conviction,
            }
        },
    ]

    # In[5]:

    # TODO: make it explicit that 1 timestep is 1 day
    simulation_parameters = {
        'T': range(30),
        'N': 1,
        'M': {
            # "sentiment_decay": 0.01, #termed mu in the state update function
            # "trigger_threshold": trigger_threshold,
            # "min_proposal_age_days": 7, # minimum periods passed before a proposal can pass,
            # "sentiment_sensitivity": 0.75,
            # 'min_supp':50, #number of tokens that must be stake for a proposal to be a candidate
            "debug": True,
            "days_to_80p_of_max_voting_weight": days_to_80p_of_max_voting_weight,
            "max_proposal_request": max_proposal_request,
        }
    }

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

    # In[7]:

    # df_final.plot("timestep", "collateral_pool", grid=True)
    # df_final.plot("timestep", "token_supply", grid=True)
    # df_final.plot("timestep", "funding_pool", grid=True)

    # In[8]:

    # import matplotlib.pyplot as plt
    # supporters = get_edges_by_type(network, 'support')
    # influencers = get_edges_by_type(network, 'influence')
    # competitors = get_edges_by_type(network, 'conflict')

    # nx.draw_kamada_kawai(network, nodelist = get_participants(network), edgelist=influencers)
    # plt.title('Participants Social Network')

    # In[9]:

    # For the Flask backend
    result = {
        "timestep": list(df_final["timestep"]),
        "funding_pool": list(df_final["funding_pool"]),
        "token_supply": list(df_final["token_supply"]),
        "collateral": list(df_final["collateral_pool"])
    }
    return result


# In[2]:
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
