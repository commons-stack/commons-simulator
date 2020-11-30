import pandas as pd
from cadCAD.configuration import Experiment
from cadCAD.configuration.utils import config_sim
from cadCAD.engine import ExecutionContext, ExecutionMode, Executor
from cadCAD import configs

import unittest
import numpy as np

from utils import (new_probability_func, new_exponential_func, new_gamma_func,
                   new_random_number_func, new_choice_func)
from hatch import create_token_batches, Commons
from network_utils import bootstrap_network, get_participants
from simulation import (CommonsSimulationConfiguration,
                        partial_state_update_blocks)


def bootstrap_simulation(c: CommonsSimulationConfiguration):
    random_seed = 1
    probability_func = new_probability_func(random_seed)
    exponential_func = new_exponential_func(random_seed)
    gamma_func = new_gamma_func(random_seed)
    random_number_func = new_random_number_func(random_seed)
    choice_func = new_choice_func(random_seed)

    contributions = [c.random_number_func() * 10e5 for i in range(c.hatchers)]
    cliff_days, halflife_days = c.cliff_and_halflife()
    token_batches, initial_token_supply = create_token_batches(
        contributions, 0.1, cliff_days, halflife_days)

    commons = Commons(sum(contributions), initial_token_supply,
                      hatch_tribute=c.hatch_tribute,
                      exit_tribute=c.exit_tribute, kappa=c.kappa)
    network = bootstrap_network(
        token_batches, c.proposals, commons._funding_pool,
        commons._token_supply, c.max_proposal_request, c.probability_func,
        c.random_number_func, c.gamma_func, c.exponential_func)

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
            "debug": False,
            "alpha_days_to_80p_of_max_voting_weight": c.alpha(),
            "max_proposal_request": c.max_proposal_request,
            "random_seed": random_seed,
            "probability_func": probability_func,
            "exponential_func": exponential_func,
            "gamma_func": gamma_func,
            "random_number_func": random_number_func,
            "choice_func": choice_func
        }
    }

    return initial_conditions, simulation_parameters


def run_simulation(c: CommonsSimulationConfiguration):
    initial_conditions, simulation_parameters = bootstrap_simulation(c)

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
    return result, df_final


class TestParticipant(unittest.TestCase):
    def setUp(self):
        c = CommonsSimulationConfiguration()
        results, df_final = run_simulation(c)
        self.df_final = df_final

    def test_participant_token_batch_age_is_updated_every_timestep(self):
        """
        Test that the age of the Participants' token batch is updated every
        timestep. The test checks if the older token batch age has the same age
        of the simulation (timestep). It considers that at least one
        participant stays in the commons from the beginning to the end of the
        simulation.
        """
        for index, row in self.df_final.iterrows():
            timestep = row['timestep']
            network = row['network']
            participants = get_participants(network)

        participants_token_batch_ages = []
        for i, participant in participants:
            participants_token_batch_ages.append(participant.holdings.age_days)
        # Check if the older token batch has the same age of the simulation
        self.assertEqual(max(participants_token_batch_ages), timestep)
